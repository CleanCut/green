from __future__ import unicode_literals
from __future__ import print_function
from collections import OrderedDict
import logging
import multiprocessing
from multiprocessing.pool import Pool
import sys
import time
import traceback

from unittest.signals import registerResult
from unittest import TestCase
import warnings

from green.output import Colors, debug, GreenStream
from green.version import pretty_version
from green.loader import getTests

try: # pragma nocover
    import html
    escape = html.escape
except: # pragma nocover
    import cgi
    escape = cgi.escape



class ProtoTestResult():


    def __init__(self):
        self.shouldStop = False
        # Individual lists
        self.errors              = []
        self.expectedFailures    = []
        self.failures            = []
        self.passing             = []
        self.skipped             = []
        self.unexpectedSuccesses = []


    def __repr__(self): # pragma: no cover
        return (
                "errors" + str(self.errors) + ', ' +
                "expectedFailures" + str(self.expectedFailures) + ', ' +
                "failures" + str(self.failures) + ', ' +
                "passing" + str(self.passing) + ', ' +
                "skipped" + str(self.skipped) + ', ' +
                "unexpectedSuccesses" + str(self.unexpectedSuccesses))


    def startTest(self, test):
        "Called before each test runs"


    def stopTest(self, test):
        "Called after each test runs"


    def addSuccess(self, test):
        "Called when a test passed"
        self.passing.append(test)


    def addError(self, test, err):
        "Called when a test raises an exception"
        self.errors.append((test, traceback.format_exception(*err)))


    def addFailure(self, test, err):
        "Called when a test fails a unittest assertion"
        self.failures.append((test, traceback.format_exception(*err)))


    def addSkip(self, test, reason):
        "Called when a test is skipped"
        self.skipped.append((test, reason))


    def addExpectedFailure(self, test, err):
        "Called when a test fails, and we expeced the failure"
        self.expectedFailures.append((test, traceback.format_exception(*err)))


    def addUnexpectedSuccess(self, test):
        "Called when a test passed, but we expected a failure"
        self.unexpectedSuccesses.append(test)



class GreenTestResult():
    "Aggregates test results and outputs them to a stream."


    def __init__(self, stream, descriptions, verbosity, html=False,
            termcolor=None):
        """stream, descriptions, and verbosity are as in
        unittest.runner.TextTestRunner.
        """
        self.stream       = stream
        self.showAll      = verbosity > 1
        self.dots         = verbosity == 1
        self.verbosity    = verbosity
        self.descriptions = descriptions
        self.colors       = Colors(termcolor, html)
        self.last_module  = ''
        self.last_class   = ''
        self.shouldStop   = False
        self.testsRun     = 0
        # Individual lists
        self.errors              = []
        self.expectedFailures    = []
        self.failures            = []
        self.passing             = []
        self.skipped             = []
        self.unexpectedSuccesses = []
        # Combination of all errors and failures
        self.all_errors = []


    def addProto(self, proto):
        if getattr(proto, 'passing', None) == None:
            print(proto)
        else:
            for test, err in proto.errors:
                self.startTest(test)
                self.addError(test, err)
            for test, err in proto.expectedFailures:
                self.startTest(test)
                self.addExpectedFailure(test, err)
            for test, err in proto.failures:
                self.startTest(test)
                self.addFailure(test, err)
            for test in proto.passing:
                self.startTest(test)
                self.addSuccess(test)
            for test, reason in proto.skipped:
                self.startTest(test)
                self.addSkip(test, reason)
            for test in proto.unexpectedSuccesses:
                self.startTest(test)
                self.addUnexpectedSuccess(test)


    def startTestRun(self):
        "Called once before any tests run"
        self.startTime = time.time()
        # Really verbose information
        if self.colors.html:
            self.stream.write(
                    '<div style="font-family: Monaco, \'Courier New\', monospace; color: rgb(170,170,170); background: rgb(0,0,0); padding: 14px;">')
        if self.verbosity > 2:
            self.stream.writeln(self.colors.bold(pretty_version() + "\n"))


    def stopTestRun(self):
        "Called once after all tests have run"
        self.stopTime = time.time()
        self.timeTaken = self.stopTime - self.startTime
        self.printErrors()
        if self.testsRun:
            self.stream.writeln()
        self.stream.writeln("Ran %s test%s in %ss" %
            (self.colors.bold(str(self.testsRun)),
            self.testsRun != 1 and "s" or "",
            self.colors.bold("%.3f" % self.timeTaken)))
        self.stream.writeln()
        results = [
            (self.errors, 'errors', self.colors.error),
            (self.expectedFailures, 'expected_failures',
                self.colors.expectedFailure),
            (self.failures, 'failures', self.colors.failing),
            (self.passing, 'passes', self.colors.passing),
            (self.skipped, 'skips', self.colors.skipped),
            (self.unexpectedSuccesses, 'unexpected_successes',
                self.colors.unexpectedSuccess),
        ]
        stats = []
        for obj_list, name, color_func in results:
            if obj_list:
                stats.append("{}={}".format(name, color_func(str(len(obj_list)))))
        if not stats:
            self.stream.writeln(self.colors.passing("No Tests Found"))
        else:
            grade = self.colors.passing('OK')
            if self.errors or self.failures:
                grade = self.colors.failing('FAILED')
            self.stream.writeln("{} ({})".format(grade, ', '.join(stats)))
        if self.colors.html:
            self.stream.writeln('</div>')


    def startTest(self, test):
        "Called before the start of each test"
        self.testsRun += 1

        # Get our bearings
        current_module = test.__module__
        current_class  = test.__class__.__name__

        # Output
        if self.showAll:
            # Module...if it changed.
            if current_module != self.last_module:
                self.stream.writeln(self.colors.moduleName(current_module))
            # Class...if it changed.
            if current_class != self.last_class:
                self.stream.writeln(self.colors.className(
                    self.stream.formatText(current_class, indent=1)))
            # Test name or description
            self.test_output_line = self._testDescription(test)
            if not self.colors.html:
                # In the terminal, we will write a placeholder, and then
                # rewrite it in color after the test has run.
                self.stream.write(
                    self.colors.bold(
                        self.stream.formatLine(self.test_output_line, indent=2)))
            self.stream.flush()

        # Set state for next time
        if current_module != self.last_module:
            self.last_module = current_module
        if current_class != self.last_class:
            self.last_class = current_class


    def stopTest(self, test):
        "Called after the end of each test"


    def _testDescription(self, test):
        return test.shortDescription() or str(test).split()[0]


    def _reportOutcome(self, test, outcome_char, color_func, err=None,
            reason=''):
        if self.showAll:
            # Move the cursor back to the start of the line in terminal mode
            if not self.colors.html:
                self.stream.write('\r')
            # Escape the HTML that may be in the docstring
            if self.colors.html:
                self.test_output_line = escape(self.test_output_line)
            self.stream.write(
                color_func(
                    self.stream.formatLine(
                        self.test_output_line,
                        indent=2,
                        outcome_char=outcome_char)
                )
            )
            if reason:
                self.stream.write(color_func(' -- ' + reason))
            self.stream.writeln()
            self.stream.flush()
        elif self.dots:
            self.stream.write(color_func(outcome_char))
            self.stream.flush()


    def addSuccess(self, test):
        "Called when a test passed"
        self.passing.append(test)
        self._reportOutcome(test, '.', self.colors.passing)


    def addError(self, test, err):
        "Called when a test raises an exception"
        self.errors.append(test)
        self.all_errors.append((test, self.colors.error, 'Error', err))
        self._reportOutcome(test, 'E', self.colors.error, err)


    def addFailure(self, test, err):
        "Called when a test fails a unittest assertion"
        self.failures.append(test)
        self.all_errors.append((test, self.colors.error, 'Failure', err))
        self._reportOutcome(test, 'F', self.colors.failing, err)


    def addSkip(self, test, reason):
        "Called when a test is skipped"
        self.skipped.append(test)
        self._reportOutcome(
                test, 's', self.colors.skipped, reason=reason)


    def addExpectedFailure(self, test, err):
        "Called when a test fails, and we expeced the failure"
        self.expectedFailures.append(test)
        self._reportOutcome(test, 'x', self.colors.expectedFailure, err)


    def addUnexpectedSuccess(self, test):
        "Called when a test passed, but we expected a failure"
        self.unexpectedSuccesses.append(test)
        self._reportOutcome(test, 'u', self.colors.unexpectedSuccess)


    def printErrors(self):
        "Print a list of all tracebacks from errors and failures"
        if not self.all_errors:
            return
        if self.dots:
            self.stream.writeln()
        for (test, color_func, outcome, err) in self.all_errors:
            # Header Line
            self.stream.writeln(
                    '\n' + color_func(outcome) +
                    ' in ' + self.colors.bold(str(test).split()[0]) +
                    ' from ' + str(test).split()[1].strip('()'))

            # Frame Line
            relevant_frames = []
            if issubclass(type(err), Exception) or (type(err) == tuple):
                iterable = enumerate(traceback.format_exception(*err))
            else:
                iterable = enumerate(err)
            for i, frame in iterable:
                debug('\n' + '*' * 30 + "Frame {}:".format(i) + '*' * 30
                      + "\n{}".format(self.colors.yellow(frame)), level = 3)
                # Ignore useless frames
                if self.verbosity < 4:
                    if frame.strip() == "Traceback (most recent call last):":
                        continue
                reindented_lines = []
                # If we're in html, space-based indenting needs to be converted.
                if self.colors.html:
                    for line in frame.split('\n'):
                        frame_indent = 0
                        while line[:2] == '  ':
                            line = line[2:]
                            frame_indent += 1
                        line = self.stream.formatLine(line, indent=frame_indent)
                        reindented_lines.append(line)
                    frame = "\n".join(reindented_lines)
                # Done with this frame, capture it.
                relevant_frames.append(frame)
            self.stream.write(''.join(relevant_frames))


    def wasSuccessful(self):
        "Tells whether or not the overall run was successful"
        return len(self.all_errors) == 0



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
    result = ProtoTestResult()
    try:
        suite = getTests(test_name)
        suite.run(result)
    except:
        err = sys.exc_info()
        result.addError('a test', err)
    return result



def getSuiteDict(item, suite_dict=OrderedDict()):
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
                                pool_runner, (test,), callback=result.addProto)
                    pool.close()
                    pool.join()

            result.stopTestRun()

        return result
