from __future__ import unicode_literals
from __future__ import print_function
from collections import OrderedDict
import sys

from unittest.signals import registerResult
from unittest import TestCase
import warnings

try: # pragma: no cover
    import coverage
except: # pragma: no cover
    coverage = None

from green.output import GreenStream
from green.result import GreenTestResult
from green.subprocess import LoggingDaemonlessPool, PoolRunner



def getSuiteDict(item, suite_dict=None):
    if suite_dict == None:
        suite_dict = OrderedDict()
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
                 warnings=None, html=None, termcolor=None, subprocesses=0,
                 run_coverage=False, omit=[]):
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
        self.run_coverage = run_coverage
        self.omit = omit


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
                pool = LoggingDaemonlessPool(processes=self.subprocesses)
                if tests:
                    for class_name in tests:
                        for index, test in enumerate(tests[class_name]):
                            if self.run_coverage:
                                coverage_number = index + 1
                            else:
                                coverage_number = None
                            pool.apply_async(
                                PoolRunner, (test, coverage_number, self.omit),
                                callback=result.addProtoTestResult)
                    pool.close()
                    pool.join()

            result.stopTestRun()

        return result
