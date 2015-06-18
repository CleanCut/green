import logging
import multiprocessing
from multiprocessing.pool import Pool
import random
import shutil
import sys
import tempfile
import traceback

try: # pragma: no cover
    import coverage
except: # pragma: no cover
    coverage = None

from green.result import ProtoTest, ProtoTestResult
from green.loader import loadTargets


class SubprocessLogger(object):
    """I am used by LoggingDaemonlessPool to get crash output out to the
    logger, instead of having subprocess crashes be silent"""


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
    """I am used by LoggingDaemonlessPool to make pool workers NOT run in
    daemon mode (daemon mode subprocess can't launch their own subprocesses)"""


    def _get_daemon(self):
        return False


    def _set_daemon(self, value):
        pass


    # 'daemon' attribute needs to always return False
    daemon = property(_get_daemon, _set_daemon)





class LoggingDaemonlessPool(Pool):
    "I use SubprocessLogger and DaemonlessProcess to make a pool of workers."


    Process = DaemonlessProcess


    def apply_async(self, func, args=(), kwds={}, callback=None):
        return Pool.apply_async(
                self, SubprocessLogger(func), args, kwds, callback)

#-------------------------------------------------------------------------------
# START of Worker Finalization Monkey Patching
#
# I started with code from cpython/Lib/multiprocessing/pool.py from version
# 3.5.0a4+ of the main python mercurial repository.  Then altered it to run on
# 2.7+ and added the finalizer/finalargs parameter handling.
    _wrap_exception = True

    def __init__(self, processes=None, initializer=None, initargs=(),
                 maxtasksperchild=None, context=None, finalizer=None,
                 finalargs=()):
        self._finalizer = finalizer
        self._finalargs = finalargs
        super(LoggingDaemonlessPool, self).__init__(processes, initializer,
                initargs, maxtasksperchild)


    def _repopulate_pool(self):
        """Bring the number of pool processes up to the specified number,
        for use after reaping workers which have exited.
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
from multiprocessing.pool import MaybeEncodingError

# Python 2 and 3 raise a different error when they exit
if platform.python_version_tuple()[0] == '2':
    PortableOSError = IOError
else:
    PortableOSError = OSError


def worker(inqueue, outqueue, initializer=None, initargs=(), maxtasks=None,
           wrap_exception=False, finalizer=None, finalargs=()):
    assert maxtasks is None or (type(maxtasks) == int and maxtasks > 0)
    put = outqueue.put
    get = inqueue.get
    if hasattr(inqueue, '_writer'):
        inqueue._writer.close()
        outqueue._reader.close()

    if initializer is not None:
        initializer(*initargs)

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
        finalizer(*finalargs)

    util.debug('worker exiting after %d tasks' % completed)

# Unmodified (see above)
class RemoteTraceback(Exception):
    def __init__(self, tb):
        self.tb = tb
    def __str__(self):
        return self.tb

# Unmodified (see above)
class ExceptionWithTraceback:
    def __init__(self, exc, tb):
        tb = traceback.format_exception(type(exc), exc, tb)
        tb = ''.join(tb)
        self.exc = exc
        self.tb = '\n"""\n%s"""' % tb
    def __reduce__(self):
        return rebuild_exc, (self.exc, self.tb)

# Unmodified (see above)
def rebuild_exc(exc, tb):
    exc.__cause__ = RemoteTraceback(tb)
    return exc

multiprocessing.pool.worker = worker
# END of Worker Finalization Monkey Patching
#-------------------------------------------------------------------------------

def poolRunner(test_name, coverage_number=None, omit_patterns=[]):
    "I am the function that pool worker subprocesses run.  I run one unit test."
    # Each pool worker gets his own temp directory, to avoid having tests that
    # are used to taking turns using the same temp file name from interfering
    # with eachother.  So long as the test doesn't use a hard-coded temp
    # directory, anyway.
    saved_tempdir = tempfile.tempdir
    tempfile.tempdir = tempfile.mkdtemp()

    # Each pool starts its own coverage, later combined by the main process.
    if coverage_number and coverage:
        cov = coverage.coverage(
                data_file='.coverage.{}_{}'.format(
                    coverage_number, random.randint(0, 10000)),
                omit=omit_patterns)
        cov.start()

    # Create a structure to return the results of this one test
    result = ProtoTestResult()
    test = None
    try:
        test = loadTargets(test_name)
    except:
        err = sys.exc_info()
        t             = ProtoTest()
        t.module      = 'green.loader'
        t.class_name  = 'N/A'
        t.description = 'Green encountered an error loading the unit test.'
        t.method_name = 'poolRunner'
        result.addError(t, err)

    try:
        test.run(result)
    except:
        # Some frameworks like testtools record the error AND THEN let it
        # through to crash things.  So we only need to manufacture another error
        # if the underlying framework didn't, but either way we don't want to
        # crash.
        if not result.errors:
            err = sys.exc_info()
            t             = ProtoTest()
            t.module      = 'green.runner'
            t.class_name  = 'N/A'
            t.description = 'Green encountered an exception not caught by the underlying test framework.'
            t.method_name = 'poolRunner'
            result.addError(t, err)

    # Finish coverage
    if coverage_number and coverage:
        cov.stop()
        cov.save()

    # Restore the state of the temp directory
    shutil.rmtree(tempfile.tempdir)
    tempfile.tempdir = saved_tempdir
    return result
