from __future__ import unicode_literals
from __future__ import print_function

from unittest.signals import registerResult
import warnings

try: # pragma: no cover
    import coverage
except: # pragma: no cover
    coverage = None

from green.loader import toProtoTestList
from green.output import GreenStream
from green.result import GreenTestResult
from green.subprocess import LoggingDaemonlessPool, poolRunner



class GreenTestRunner():
    "A test runner class that displays results in Green's clean style."


    def __init__(self, stream, descriptions=True, verbosity=1,
                 warnings=None, html=None, termcolor=None, subprocesses=0,
                 run_coverage=False, omit=[]):
        """
        stream - Any stream passed in will be wrapped in a GreenStream
        """
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
                tests = toProtoTestList(suite)
                pool = LoggingDaemonlessPool(processes=self.subprocesses)
                if tests:
                    async_responses = []
                    for index, test in enumerate(tests):
                        if self.run_coverage:
                            coverage_number = index + 1
                        else:
                            coverage_number = None
                        async_responses.append(pool.apply_async(
                            poolRunner,
                            (test.dotted_name, coverage_number, self.omit)))
                    pool.close()
                    for test, async_response in zip(tests, async_responses):
                        # Prints out the white 'processing...' version of the output
                        result.startTest(test)
                        # This blocks until the worker who is processing this
                        # particular test actually finishes
                        result.addProtoTestResult(async_response.get())
                pool.terminate()
                pool.join()

            result.stopTestRun()

        return result
