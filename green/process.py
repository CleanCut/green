"""
Handle running unittests suites in parallel.
"""

from __future__ import annotations

import logging
import multiprocessing
import multiprocessing.pool
from multiprocessing.pool import MaybeEncodingError  # type: ignore
from multiprocessing.pool import Pool
from multiprocessing import util  # type: ignore

import os
import random
import sys
import tempfile
import traceback
from typing import (
    Type,
    TYPE_CHECKING,
    Union,
    Tuple,
    Callable,
    Iterable,
    Mapping,
    Any,
    TypeVar,
)

import coverage

from green.exceptions import InitializerOrFinalizerError
from green.loader import GreenTestLoader
from green.result import proto_test, ProtoTest, ProtoTestResult

if TYPE_CHECKING:
    from types import TracebackType
    from queue import Queue

    from multiprocessing.context import SpawnContext, SpawnProcess
    from multiprocessing.pool import ApplyResult
    from multiprocessing.queues import SimpleQueue

    from green.suite import GreenTestSuite
    from green.runner import InitializerOrFinalizer
    from green.result import RunnableTestT

    ExcInfoType = Union[
        Tuple[Type[BaseException], BaseException, TracebackType],
        Tuple[None, None, None],
    ]
    _T = TypeVar("_T")


# Super-useful debug function for finding problems in the subprocesses, and it
# even works on windows
def ddebug(msg: str, err: ExcInfoType | None = None) -> None:  # pragma: no cover
    """
    err can be an instance of sys.exc_info() -- which is the latest traceback
    info
    """
    if err:
        error_string = "".join(traceback.format_exception(*err))
    else:
        error_string = ""
    sys.__stdout__.write(f"({os.getpid()}) {msg} {error_string}\n")
    sys.__stdout__.flush()


class ProcessLogger:
    """
    I am used by LoggingDaemonlessPool to get crash output out to the logger,
    instead of having process crashes be silent.
    """

    def __init__(self, callable: Callable) -> None:
        self.__callable = callable

    def __call__(self, *args, **kwargs) -> Any:
        try:
            return self.__callable(*args, **kwargs)
        except Exception:
            # Here we add some debugging help. If multiprocessing's
            # debugging is on, it will arrange to log the traceback
            logger = multiprocessing.get_logger()
            if not logger.handlers:
                logger.addHandler(logging.StreamHandler())
            logger.error(traceback.format_exc())
            logger.handlers[0].flush()
            # Re-raise the original exception so the Pool worker can
            # clean up
            raise


class LoggingDaemonlessPool(Pool):
    """
    I make a pool of workers which can get crash output to the logger, run processes not as daemons,
    and which run finalizers.
    """

    _wrap_exception: bool = True

    @staticmethod
    def Process(ctx: SpawnContext, *args: Any, **kwargs: Any) -> SpawnProcess:
        return ctx.Process(daemon=False, *args, **kwargs)

    def apply_async(
        self,
        func: Callable[[Any, Any], _T],  # should be the poolRunner method.
        args: Iterable = (),
        kwargs: Mapping[str, Any] | None = None,
        callback: Callable[[_T], Any] | None = None,
        error_callback: Callable[[BaseException], Any] | None = None,
    ) -> ApplyResult[_T]:
        if kwargs is None:
            kwargs = {}
        return super().apply_async(
            ProcessLogger(func), args, kwargs, callback, error_callback
        )

    def __init__(
        self,
        processes: int | None = None,
        initializer: Callable | None = None,
        initargs: Iterable[Any] = (),
        maxtasksperchild: int | None = None,
        context: Any | None = None,
        # Green specific:
        finalizer: Callable | None = None,
        finalargs: Iterable[Any] = (),
    ):
        self._finalizer = finalizer
        self._finalargs = finalargs
        super().__init__(processes, initializer, initargs, maxtasksperchild, context)

    def _repopulate_pool(self):
        return self._repopulate_pool_static(
            self._ctx,
            self.Process,
            self._processes,
            self._pool,
            self._inqueue,
            self._outqueue,
            self._initializer,
            self._initargs,
            self._maxtasksperchild,
            self._wrap_exception,
            self._finalizer,
            self._finalargs,
        )

    @staticmethod
    def _repopulate_pool_static(
        ctx: SpawnContext,
        Process: Callable,  # LoggingDaemonlessPool.Process
        processes: int,
        pool: list[Callable],  # list of LoggingDaemonlessPool.Process
        inqueue: SimpleQueue,
        outqueue: SimpleQueue,
        initializer: InitializerOrFinalizer,
        initargs: tuple,
        maxtasksperchild: int | None,
        wrap_exception: bool,
        finalizer: InitializerOrFinalizer,
        finalargs: tuple,
    ) -> None:
        """
        Bring the number of pool processes up to the specified number,
        for use after reaping workers which have exited.
        """
        for i in range(processes - len(pool)):
            w = Process(
                ctx,
                target=worker,
                args=(
                    inqueue,
                    outqueue,
                    initializer,
                    initargs,
                    maxtasksperchild,
                    wrap_exception,
                    finalizer,
                    finalargs,
                ),
            )
            w.name = w.name.replace("Process", "PoolWorker")
            w.start()
            pool.append(w)
            util.debug("added worker")


def worker(
    inqueue: SimpleQueue,
    outqueue: SimpleQueue,
    initializer: InitializerOrFinalizer | None = None,
    initargs: tuple = (),
    maxtasks: int | None = None,
    wrap_exception: bool = False,
    finalizer: Callable | None = None,
    finalargs: tuple = (),
):  # pragma: no cover
    # TODO: revisit this assert; these statements are skipped by the python
    #  compiler in optimized mode.
    assert maxtasks is None or (isinstance(maxtasks, int) and maxtasks > 0)
    put = outqueue.put
    get = inqueue.get

    writer = getattr(inqueue, "_writer", None)
    if writer is not None:
        writer.close()
    reader = getattr(outqueue, "_reader", None)
    if reader is not None:
        reader.close()

    if initializer is not None:
        try:
            initializer(*initargs)
        except InitializerOrFinalizerError as e:
            print(str(e))

    completed = 0
    while maxtasks is None or (maxtasks and completed < maxtasks):
        try:
            task = get()
        except (EOFError, OSError):
            util.debug("worker got EOFError or OSError -- exiting")
            break

        if task is None:
            util.debug("worker got sentinel -- exiting")
            break

        job, i, func, args, kwds = task
        try:
            result = (True, func(*args, **kwds))
        except Exception as result_error:
            if wrap_exception:
                result_error = ExceptionWithTraceback(
                    result_error, result_error.__traceback__
                )
            result = (False, result_error)
        try:
            put((job, i, result))
        except Exception as e:
            wrapped = MaybeEncodingError(e, result[1])
            util.debug("Possible encoding error while sending result: %s" % (wrapped))
            put((job, i, (False, wrapped)))
        completed += 1

    if finalizer:
        try:
            finalizer(*finalargs)
        except InitializerOrFinalizerError as e:
            print(str(e))

    util.debug("worker exiting after %d tasks" % completed)


# Unmodified (see above)
class RemoteTraceback(Exception):  # pragma: no cover
    def __init__(self, tb: str):
        self.tb = tb

    def __str__(self) -> str:
        return self.tb


# Unmodified (see above)
class ExceptionWithTraceback(Exception):  # pragma: no cover
    def __init__(self, exc: BaseException, tb: TracebackType | None):
        tb_lines = traceback.format_exception(type(exc), exc, tb)
        tb_text = "".join(tb_lines)
        self.exc = exc
        self.tb = '\n"""\n%s"""' % tb_text

    def __reduce__(self) -> Tuple[Callable, Tuple[BaseException, str]]:
        return rebuild_exc, (self.exc, self.tb)


# Unmodified (see above)
def rebuild_exc(exc: BaseException, tb: str):  # pragma: no cover
    exc.__cause__ = RemoteTraceback(tb)
    return exc


multiprocessing.pool.worker = worker  # type: ignore
# END of Worker Finalization Monkey Patching
# -----------------------------------------------------------------------------


def poolRunner(
    target: str,
    queue: Queue,
    coverage_number: int | None = None,
    omit_patterns: str | Iterable[str] | None = None,
    cov_config_file: bool = True,
) -> None:  # pragma: no cover
    """
    I am the function that pool worker processes run.  I run one unit test.

    coverage_config_file is a special option that is either a string specifying
    the custom coverage config file or the special default value True (which
    causes coverage to search for it's standard config files).
    """
    # Each pool worker gets his own temp directory, to avoid having tests that
    # are used to taking turns using the same temp file name from interfering
    # with eachother.  So long as the test doesn't use a hard-coded temp
    # directory, anyway.
    saved_tempdir = tempfile.tempdir
    tempfile.tempdir = tempfile.mkdtemp()

    def raise_internal_failure(msg: str) -> None:
        err = sys.exc_info()
        t = ProtoTest()
        t.module = "green.loader"
        t.class_name = "N/A"
        t.description = msg
        t.method_name = "poolRunner"
        result.startTest(t)
        result.addError(t, err)
        result.stopTest(t)
        queue.put(result)
        cleanup()

    def cleanup() -> None:
        # Restore the state of the temp directory
        tempfile.tempdir = saved_tempdir
        queue.put(None)
        # Finish coverage
        if coverage_number:
            cov.stop()
            cov.save()

    # Each pool starts its own coverage, later combined by the main process.
    if coverage_number:
        cov = coverage.coverage(
            data_file=".coverage.{}_{}".format(
                coverage_number, random.randint(0, 10000)
            ),
            omit=omit_patterns,
            config_file=cov_config_file,
        )
        cov._warn_no_data = False
        cov.start()

    # What to do each time an individual test is started
    already_sent = set()

    def start_callback(test: RunnableTestT) -> None:
        # Let the main process know what test we are starting
        test_proto = proto_test(test)
        if test_proto not in already_sent:
            queue.put(test_proto)
            already_sent.add(test_proto)

    def finalize_callback(test_result: ProtoTestResult) -> None:
        # Let the main process know what happened with the test run
        queue.put(test_result)

    result = ProtoTestResult(start_callback, finalize_callback)
    test: GreenTestSuite | None
    try:
        loader = GreenTestLoader()
        test = loader.loadTargets(target)
    except:
        raise_internal_failure("Green encountered an error loading the unit test.")
        return

    if test is not None and getattr(test, "run", False):
        # Loading was successful, lets do this
        try:
            test.run(result)
            # If your class setUpClass(self) method crashes, the test doesn't
            # raise an exception, but it does add an entry to errors.  Some
            # other things add entries to errors as well, but they all call the
            # finalize callback.
            if (
                result
                and (not result.finalize_callback_called)
                and getattr(result, "errors", False)
            ):
                queue.put(test)
                queue.put(result)
        except:
            # Some frameworks like testtools record the error AND THEN let it
            # through to crash things.  So we only need to manufacture another
            # error if the underlying framework didn't, but either way we don't
            # want to crash.
            if result.errors:
                queue.put(result)
            else:
                try:
                    err = sys.exc_info()
                    result.startTest(test)
                    result.addError(test, err)
                    result.stopTest(test)
                    queue.put(result)
                except:
                    raise_internal_failure(
                        "Green encountered an error when running the test."
                    )
                    return
    else:
        # loadTargets() returned an object without a run() method, probably
        # None
        description = (
            f'Test loader returned an un-runnable object.  Is "{target}" '
            "importable from your current location?  Maybe you "
            "forgot an __init__.py in your directory?  Unrunnable "
            f"object looks like: {test} of type {type(test)} with dir {dir(test)}"
        )
        no_run_error = (TypeError, TypeError(description), None)
        t = ProtoTest()
        t.description = description
        target_list = target.split(".")
        if len(target_list) > 1:
            t.module = ".".join(target_list[:-2])
            t.class_name = target_list[-2]
            t.method_name = target_list[-1]
        else:
            t.module = target
            t.class_name = "UnknownClass"
            t.method_name = "unknown_method"
        result.startTest(t)
        # Ignoring that no_run_error traceback is None.
        result.addError(t, no_run_error)  # type: ignore[arg-type]
        result.stopTest(t)
        queue.put(result)

    cleanup()
