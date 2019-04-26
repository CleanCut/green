from __future__ import unicode_literals
import logging
import multiprocessing
from multiprocessing.pool import Pool
import random
import shutil
import sys
import tempfile
import traceback

import coverage

from green.exceptions import InitializerOrFinalizerError
from green.loader import GreenTestLoader
from green.result import proto_test, ProtoTest, ProtoTestResult


# Super-useful debug function for finding problems in the subprocesses, and it
# even works on windows
def ddebug(msg, err=None):  # pragma: no cover
    """
    err can be an instance of sys.exc_info() -- which is the latest traceback
    info
    """
    import os
    if err:
        err = ''.join(traceback.format_exception(*err))
    else:
        err = ''
    sys.__stdout__.write("({}) {} {}".format(os.getpid(), msg, err)+'\n')
    sys.__stdout__.flush()


class ProcessLogger(object):
    """
    I am used by LoggingDaemonlessPool to get crash output out to the logger,
    instead of having process crashes be silent
    """

    def __init__(self, callable):
        self.__callable = callable

    def __call__(self, *args, **kwargs):
        try:
            result = self.__callable(*args, **kwargs)
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

        # It was fine, give a normal answer
        return result


class DaemonlessProcess(multiprocessing.Process):
    """
    I am used by LoggingDaemonlessPool to make pool workers NOT run in
    daemon mode (daemon mode process can't launch their own subprocesses)
    """

    def _get_daemon(self):
        return False

    def _set_daemon(self, value):
        pass

    # 'daemon' attribute needs to always return False
    daemon = property(_get_daemon, _set_daemon)


class LoggingDaemonlessPool(Pool):
    """
    I use ProcessLogger and DaemonlessProcess to make a pool of workers.
    """

    Process = DaemonlessProcess

    def apply_async(self, func, args=(), kwds={}, callback=None):
        return Pool.apply_async(
                self, ProcessLogger(func), args, kwds, callback)

    # -------------------------------------------------------------------------
    # START of Worker Finalization Monkey Patching
    #
    # I started with code from cpython/Lib/multiprocessing/pool.py from version
    # 3.5.0a4+ of the main python mercurial repository.  Then altered it to run
    # on 2.7+ and added the finalizer/finalargs parameter handling.
    _wrap_exception = True

    def __init__(self, processes=None, initializer=None, initargs=(),
                 maxtasksperchild=None, context=None, finalizer=None,
                 finalargs=()):
        self._finalizer = finalizer
        self._finalargs = finalargs
        super(LoggingDaemonlessPool, self).__init__(processes, initializer,
                                                    initargs, maxtasksperchild)

    def _repopulate_pool(self):
        """
        Bring the number of pool processes up to the specified number, for use
        after reaping workers which have exited.
        """
        for i in range(self._processes - len(self._pool)):
            w = self.Process(target=worker,
                             args=(self._inqueue, self._outqueue,
                                   self._initializer,
                                   self._initargs, self._maxtasksperchild,
                                   self._wrap_exception,
                                   self._finalizer,
                                   self._finalargs)
                             )
            self._pool.append(w)
            w.name = w.name.replace('Process', 'PoolWorker')
            w.daemon = True
            w.start()
            util.debug('added worker')


import platform
import multiprocessing.pool
from multiprocessing import util
try:
    from multiprocessing.pool import MaybeEncodingError
except:  # pragma: no cover
    # Python 2.7.4 introduced this class.  If we're on Python 2.7.0 to 2.7.3
    # then we'll have to define it ourselves. :-/
    class MaybeEncodingError(Exception):
        """Wraps possible unpickleable errors, so they can be
        safely sent through the socket."""

        def __init__(self, exc, value):
            self.exc = repr(exc)
            self.value = repr(value)
            super(MaybeEncodingError, self).__init__(self.exc, self.value)

        def __str__(self):
            return "Error sending result: '%s'. Reason: '%s'" % (self.value,
                                                                 self.exc)

        def __repr__(self):
            return "<MaybeEncodingError: %s>" % str(self)


# Python 2 and 3 raise a different error when they exit
if platform.python_version_tuple()[0] == '2':  # pragma: no cover
    PortableOSError = IOError
else:  # pragma: no cover
    PortableOSError = OSError


def worker(inqueue, outqueue, initializer=None, initargs=(), maxtasks=None,
           wrap_exception=False, finalizer=None, finalargs=()):  # pragma: no cover
    assert maxtasks is None or (type(maxtasks) == int and maxtasks > 0)
    put = outqueue.put
    get = inqueue.get
    if hasattr(inqueue, '_writer'):
        inqueue._writer.close()
        outqueue._reader.close()

    if initializer is not None:
        try:
            initializer(*initargs)
        except InitializerOrFinalizerError as e:
            print(str(e))

    completed = 0
    while maxtasks is None or (maxtasks and completed < maxtasks):
        try:
            task = get()
        except (EOFError, PortableOSError):
            util.debug('worker got EOFError or OSError -- exiting')
            break

        if task is None:
            util.debug('worker got sentinel -- exiting')
            break

        job, i, func, args, kwds = task
        try:
            result = (True, func(*args, **kwds))
        except Exception as e:
            if wrap_exception:
                e = ExceptionWithTraceback(e, e.__traceback__)
            result = (False, e)
        try:
            put((job, i, result))
        except Exception as e:
            wrapped = MaybeEncodingError(e, result[1])
            util.debug("Possible encoding error while sending result: %s" % (
                wrapped))
            put((job, i, (False, wrapped)))
        completed += 1

    if finalizer:
        try:
            finalizer(*finalargs)
        except InitializerOrFinalizerError as e:
            print(str(e))

    util.debug('worker exiting after %d tasks' % completed)


# Unmodified (see above)
class RemoteTraceback(Exception):  # pragma: no cover
    def __init__(self, tb):
        self.tb = tb

    def __str__(self):
        return self.tb


# Unmodified (see above)
class ExceptionWithTraceback:  # pragma: no cover
    def __init__(self, exc, tb):
        tb = traceback.format_exception(type(exc), exc, tb)
        tb = ''.join(tb)
        self.exc = exc
        self.tb = '\n"""\n%s"""' % tb

    def __reduce__(self):
        return rebuild_exc, (self.exc, self.tb)


# Unmodified (see above)
def rebuild_exc(exc, tb):  # pragma: no cover
    exc.__cause__ = RemoteTraceback(tb)
    return exc

multiprocessing.pool.worker = worker
# END of Worker Finalization Monkey Patching
# -----------------------------------------------------------------------------


def poolRunner(target, queue, coverage_number=None, omit_patterns=[], cov_config_file=True):  # pragma: no cover
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

    def cleanup():
        # Restore the state of the temp directory
        # TODO: Make this not necessary on macOS+Python3 (see #173)
        if sys.version_info[0] == 2:
            shutil.rmtree(tempfile.tempdir, ignore_errors=True)
        tempfile.tempdir = saved_tempdir
        queue.put(None)
        # Finish coverage
        if coverage_number:
            cov.stop()
            cov.save()

    # Each pool starts its own coverage, later combined by the main process.
    if coverage_number:
        cov = coverage.coverage(
                data_file='.coverage.{}_{}'.format(
                    coverage_number, random.randint(0, 10000)),
                omit=omit_patterns,
                config_file=cov_config_file)
        cov._warn_no_data = False
        cov.start()

    # What to do each time an individual test is started
    already_sent = set()

    def start_callback(test):
        # Let the main process know what test we are starting
        test = proto_test(test)
        if test not in already_sent:
            queue.put(test)
            already_sent.add(test)

    def finalize_callback(test_result):
        # Let the main process know what happened with the test run
        queue.put(test_result)

    result = ProtoTestResult(start_callback, finalize_callback)
    test = None
    try:
        loader = GreenTestLoader()
        test = loader.loadTargets(target)
    except:
        err = sys.exc_info()
        t             = ProtoTest()
        t.module      = 'green.loader'
        t.class_name  = 'N/A'
        t.description = 'Green encountered an error loading the unit test.'
        t.method_name = 'poolRunner'
        result.startTest(t)
        result.addError(t, err)
        result.stopTest(t)
        queue.put(result)
        cleanup()
        return

    if getattr(test, 'run', False):
        # Loading was successful, lets do this
        try:
            test.run(result)
            # If your class setUpClass(self) method crashes, the test doesn't
            # raise an exception, but it does add an entry to errors.  Some
            # other things add entries to errors as well, but they all call the
            # finalize callback.
            if result and (not result.finalize_callback_called) and getattr(result, 'errors', False):
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
                err = sys.exc_info()
                result.startTest(test)
                result.addError(test, err)
                result.stopTest(test)
                queue.put(result)
    else:
        # loadTargets() returned an object without a run() method, probably
        # None
        description = ('Test loader returned an un-runnable object.  Is "{}" '
                       'importable from your current location?  Maybe you '
                       'forgot an __init__.py in your directory?  Unrunnable '
                       'object looks like: {} of type {} with dir {}'
                       .format(target, str(test), type(test), dir(test))
                       )
        err = (TypeError, TypeError(description), None)
        t             = ProtoTest()
        target_list = target.split('.')
        t.module      = '.'.join(target_list[:-2]) if len(target_list) > 1 else target
        t.class_name  = target.split('.')[-2] if len(target_list) > 1 else 'UnknownClass'
        t.description = description
        t.method_name = target.split('.')[-1] if len(target_list) > 1 else 'unknown_method'
        result.startTest(t)
        result.addError(t, err)
        result.stopTest(t)
        queue.put(result)

    cleanup()
