from __future__ import unicode_literals
from __future__ import print_function
from collections import OrderedDict
import logging
import multiprocessing
from multiprocessing.pool import Pool
import shutil
import sys
import tempfile
import traceback

from unittest.signals import registerResult
from unittest import TestCase
import warnings

from green.loader import getTests
from green.output import GreenStream
from green.result import ProtoTest, ProtoTestResult, GreenTestResult



class LogExceptions(object):


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



class LoggingPool(Pool):


    def apply_async(self, func, args=(), kwds={}, callback=None):
        return Pool.apply_async(self, LogExceptions(func), args, kwds, callback)



def pool_runner(test_name):
    # Each pool worker gets his own temp directory, to avoid having tests that
    # are used to taking turns using the same temp file name from interfering
    # with eachother.  So long as the test doesn't use a hard-coded temp
    # directory, anyway.
    saved_tempdir = tempfile.tempdir
    tempfile.tempdir = tempfile.mkdtemp()

    # Create a structure to return the results of this one test
    result = ProtoTestResult()
    test = None
    try:
        test = getTests(test_name)
        test.run(result)
    except:
        err = sys.exc_info()
        if test:
            result.addError(test, err)
        else:
            t             = ProtoTest()
            t.module      = 'green.runner'
            t.class_name  = 'N/A'
            t.description = "Green's subprocess pool should function correctly."
            t.method_name = 'pool_runner'
            result.addError(t, err)
    # Restore the state of the temp directory
    shutil.rmtree(tempfile.tempdir)
    tempfile.tempdir = saved_tempdir
    return result



def getSuiteDict(item, suite_dict=OrderedDict()):
    # Python's lousy handling of module import failures during loader discovery
    # makes this crazy special case necessary.  See _make_failed_import_test in
    # the source code for unittest.loader
    if item.__class__.__name__ == 'ModuleImportFailure':
        exception_method = str(item).split()[0]
        getattr(item, exception_method)()
    # On to the real stuff
    if issubclass(type(item), TestCase):
        class_part = item.__module__ + '.' + item.__class__.__name__
        test_part = str(item).split(' ')[0]
        full_test = class_part + '.' + test_part
        if class_part not in suite_dict.keys():
            suite_dict[class_part] = []
        suite_dict[class_part].append(full_test)
    else:
        for i in item:
            getSuiteDict(i, suite_dict)
        return suite_dict



class GreenTestRunner():
    "A test runner class that displays results in Green's clean style."


    def __init__(self, stream=None, descriptions=True, verbosity=1,
                 warnings=None, html=None, termcolor=None, subprocesses=0):
        """
        stream - Any stream passed in will be wrapped in a GreenStream
        """
        if stream is None:
            stream = sys.stderr
        if not issubclass(GreenStream, type(stream)):
            stream = GreenStream(stream)
        self.stream = stream
        self.descriptions = descriptions
        self.verbosity = verbosity
        self.warnings = warnings
        self.html = html
        self.termcolor = termcolor
        self.subprocesses = subprocesses or None


    def run(self, suite):
        "Run the given test case or test suite."
        result = GreenTestResult(
                self.stream, self.descriptions, self.verbosity, html=self.html,
                termcolor=self.termcolor)
        registerResult(result)
        with warnings.catch_warnings():
            if self.warnings:
                # if self.warnings is set, use it to filter all the warnings
                warnings.simplefilter(self.warnings)
                # if the filter is 'default' or 'always', special-case the
                # warnings from the deprecated unittest methods to show them
                # no more than once per module, because they can be fairly
                # noisy.  The -Wd and -Wa flags can be used to bypass this
                # only when self.warnings is None.
                if self.warnings in ['default', 'always']:
                    warnings.filterwarnings('module',
                            category=DeprecationWarning,
                            message='Please use assert\w+ instead.')
            result.startTestRun()

            if self.subprocesses == 1:
                suite.run(result)
            else:
                tests = getSuiteDict(suite)
                pool = LoggingPool(processes=self.subprocesses)
                if tests:
                    for group in tests:
                        for test in tests[group]:
                            pool.apply_async(
                                pool_runner, (test,),
                                callback=result.addProtoTestResult)
                    pool.close()
                    pool.join()

            result.stopTestRun()

        return result
