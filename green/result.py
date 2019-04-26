from __future__ import unicode_literals
from __future__ import print_function

from collections import OrderedDict
from io import StringIO
from math import ceil
import sys
import time
import traceback
from unittest.result import failfast

from green.output import Colors, debug
from green.version import pretty_version

# introduced in Python 3
try:
    from shutil import get_terminal_size
except ImportError: # pragma: no cover
    from backports.shutil_get_terminal_size import get_terminal_size

terminal_width, _ignored = get_terminal_size()

def proto_test(test):
    """
    If test is a ProtoTest, I just return it.  Otherwise I create a ProtoTest
    out of test and return it.
    """
    if isinstance(test, ProtoTest):
        return test
    else:
        return ProtoTest(test)


def proto_error(err):
    """
    If err is a ProtoError, I just return it.  Otherwise I create a ProtoError
    out of err and return it.
    """
    if isinstance(err, ProtoError):
        return err
    else:
        return ProtoError(err)


class ProtoTest():
    """
    I take a full-fledged TestCase and preserve just the information we need
    and can pass between processes.
    """
    def __init__(self, test=None):
        self.module = ''
        self.class_name = ''
        self.method_name = ''
        self.docstr_part = ''
        self.subtest_part = ''
        self.is_subtest = False

        # Is this a subtest?
        if getattr(test, '_subDescription', None):
            self.is_subtest = True
            self.subtest_part = ' ' + test._subDescription()
            test = test.test_case

        # Is this a TestCase?
        if test:
            self.module      = test.__module__
            self.class_name  = test.__class__.__name__
            self.method_name = str(test).split()[0]
            # docstr_part strips initial whitespace, then combines all lines
            # into one string until the first completely blank line in the
            # docstring
            doc_segments = []
            if getattr(test, "_testMethodDoc", None):
                for line in test._testMethodDoc.lstrip().split('\n'):
                    line = line.strip()
                    if not line:
                        break
                    doc_segments.append(line)
            self.docstr_part = ' '.join(doc_segments)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return hash(self.dotted_name)

    def __str__(self):
        return self.dotted_name

    @property
    def dotted_name(self, ignored=None):
        return self.module + '.' + self.class_name + '.' + self.method_name + self.subtest_part

    def getDescription(self, verbose):
        if verbose == 2:
            return self.method_name + self.subtest_part
        elif verbose > 2:
            return (self.docstr_part + self.subtest_part) or (self.method_name + self.subtest_part)
        else:
            return ''


class ProtoError():
    """
    I take a full-fledged test error and preserve just the information we need
    and can pass between processes.
    """
    def __init__(self, err=None):
        self.traceback_lines = traceback.format_exception(*err)

    def __str__(self):
        return '\n'.join(self.traceback_lines)


class BaseTestResult(object):  # Breaks subclasses in 2.7 not inheriting object
    """
    I am inherited by ProtoTestResult and GreenTestResult.
    """
    def __init__(self, stream, colors):
        self.stdout_output = OrderedDict()
        self.stderr_errput = OrderedDict()
        self.stream = stream
        self.colors = colors

    def recordStdout(self, test, output):
        """
        Called with stdout that the suite decided to capture so we can report
        the captured output somewhere.
        """
        if output:
            test = proto_test(test)
            self.stdout_output[test] = output

    def recordStderr(self, test, errput):
        """
        Called with stderr that the suite decided to capture so we can report
        the captured "errput" somewhere.
        """
        if errput:
            test = proto_test(test)
            self.stderr_errput[test] = errput

    def displayStdout(self, test):
        """
        Displays AND REMOVES the output captured from a specific test.  The
        removal is done so that this method can be called multiple times
        without duplicating results output.
        """
        test = proto_test(test)
        if test.dotted_name in self.stdout_output:
            self.stream.write(
                "\n{} for {}\n{}".format(
                    self.colors.yellow('Captured stdout'),
                    self.colors.bold(test.dotted_name),
                    self.stdout_output[test]))
            del(self.stdout_output[test])

    def displayStderr(self, test):
        """
        Displays AND REMOVES the errput captured from a specific test.  The
        removal is done so that this method can be called multiple times
        without duplicating results errput.
        """
        test = proto_test(test)
        if test.dotted_name in self.stderr_errput:
            self.stream.write(
                "\n{} for {}\n{}".format(
                    self.colors.yellow('Captured stderr'),
                    self.colors.bold(test.dotted_name),
                    self.stderr_errput[test]))
            del(self.stderr_errput[test])


class ProtoTestResult(BaseTestResult):
    """
    I'm the TestResult object for a single unit test run in a process.
    """
    def __init__(self, start_callback=None, finalize_callback=None):
        super(ProtoTestResult, self).__init__(None, None)
        self.start_callback = start_callback
        self.finalize_callback = finalize_callback
        self.finalize_callback_called = False
        self.pickle_attrs = [
                'errors',
                'expectedFailures',
                'failures',
                'passing',
                'pickle_attrs',
                'shouldStop',
                'skipped',
                'stderr_errput',
                'stdout_output',
                'unexpectedSuccesses',
                ]
        self.failfast = False  # Because unittest inspects the attribute
        self.reinitialize()

    def reinitialize(self):
        self.shouldStop = False
        self.errors              = []
        self.expectedFailures    = []
        self.failures            = []
        self.passing             = []
        self.skipped             = []
        self.unexpectedSuccesses = []

    def __repr__(self):  # pragma: no cover
        return (
            "errors" + str(self.errors) + ', ' +
            "expectedFailures" + str(self.expectedFailures) + ', ' +
            "failures" + str(self.failures) + ', ' +
            "passing" + str(self.passing) + ', ' +
            "skipped" + str(self.skipped) + ', ' +
            "unexpectedSuccesses" + str(self.unexpectedSuccesses))

    def __getstate__(self):
        """
        Prevent the callback functions from getting pickled
        """
        result_dict = {}
        for pickle_attr in self.pickle_attrs:
            result_dict[pickle_attr] = self.__dict__[pickle_attr]
        return result_dict

    def __setstate__(self, dict):
        """
        Since the callback functions weren't pickled, we need to init them
        """
        self.__dict__.update(dict)
        self.start_callback = None
        self.finalize_callback = None

    def startTest(self, test):
        """
        Called before each test runs
        """
        test = proto_test(test)
        self.reinitialize()
        if self.start_callback:
            self.start_callback(test)

    def stopTest(self, test):
        """
        Called after each test runs
        """
        pass

    def finalize(self):
        """
        I am here so that after the GreenTestSuite has had a chance to inject
        the captured stdout/stderr back into me, I can relay that through to
        the worker process's poolRunner who will send me back up to the parent
        process.
        """
        if self.finalize_callback:
            self.finalize_callback(self)
            self.finalize_callback_called = True

    def addSuccess(self, test):
        """
        Called when a test passed
        """
        self.passing.append(proto_test(test))

    def addError(self, test, err):
        """
        Called when a test raises an exception
        """
        self.errors.append((proto_test(test), proto_error(err)))

    def addFailure(self, test, err):
        """
        Called when a test fails a unittest assertion
        """
        self.failures.append((proto_test(test), proto_error(err)))

    def addSkip(self, test, reason):
        """
        Called when a test is skipped
        """
        self.skipped.append((proto_test(test), reason))

    def addExpectedFailure(self, test, err):
        """
        Called when a test fails, and we expeced the failure
        """
        self.expectedFailures.append((proto_test(test), proto_error(err)))

    def addUnexpectedSuccess(self, test):
        """
        Called when a test passed, but we expected a failure
        """
        self.unexpectedSuccesses.append(proto_test(test))

    def addSubTest(self, test, subtest, err):
        """
        Called at the end of a subtest no matter its result.

        The test that runs the subtests is calls the other test methods to
        record its own result.  We use this method to record each subtest as a
        separate test result.  It's very meta.
        """
        if err is not None:
            if issubclass(err[0], test.failureException):
                self.addFailure(subtest, err)
            else:
                self.addError(subtest, err)



class GreenTestResult(BaseTestResult):
    """
    Aggregates test results and outputs them to a stream.
    """
    def __init__(self, args, stream):
        super(GreenTestResult, self).__init__(stream, Colors(args.termcolor))
        self.args              = args
        self.showAll           = args.verbose > 1
        self.dots              = args.verbose == 1
        self.verbose           = args.verbose
        self.last_module       = ''
        self.last_class        = ''
        self.first_text_output = ''
        self.failfast          = args.failfast
        self.shouldStop        = False
        self.testsRun          = 0
        # Individual lists
        self.errors              = []
        self.expectedFailures    = []
        self.failures            = []
        self.passing             = []
        self.skipped             = []
        self.unexpectedSuccesses = []
        # Combination of all errors and failures
        self.all_errors = []
        # For exiting non-zero if we don't reach a certain level of coverage
        self.coverage_percent = None

    def stop(self):
        self.shouldStop = True

    def tryRecordingStdoutStderr(self, test, proto_test_result):
        if proto_test_result.stdout_output.get(test, False):
            self.recordStdout(test, proto_test_result.stdout_output[test])
        if proto_test_result.stderr_errput.get(test, False):
            self.recordStderr(test, proto_test_result.stderr_errput[test])

    def addProtoTestResult(self, proto_test_result):
        for test, err in proto_test_result.errors:
            self.addError(test, err)
            self.tryRecordingStdoutStderr(test, proto_test_result)
        for test, err in proto_test_result.expectedFailures:
            self.addExpectedFailure(test, err)
            self.tryRecordingStdoutStderr(test, proto_test_result)
        for test, err in proto_test_result.failures:
            self.addFailure(test, err)
            self.tryRecordingStdoutStderr(test, proto_test_result)
        for test in proto_test_result.passing:
            self.addSuccess(test)
            self.tryRecordingStdoutStderr(test, proto_test_result)
        for test, reason in proto_test_result.skipped:
            self.addSkip(test, reason)
            self.tryRecordingStdoutStderr(test, proto_test_result)
        for test in proto_test_result.unexpectedSuccesses:
            self.addUnexpectedSuccess(test)
            self.tryRecordingStdoutStderr(test, proto_test_result)

    def startTestRun(self):
        """
        Called once before any tests run
        """
        self.startTime = time.time()
        # Really verbose information
        if self.verbose > 2:
            self.stream.writeln(self.colors.bold(pretty_version() + "\n"))

    def stopTestRun(self):
        """
        Called once after all tests have run
        """
        self.stopTime = time.time()
        self.timeTaken = self.stopTime - self.startTime
        self.printErrors()
        if self.args.run_coverage or self.args.quiet_coverage:
            from coverage.misc import CoverageException
            try:
                self.stream.writeln()
                self.args.cov.stop()
                self.args.cov.save()
                self.args.cov.combine()
                self.args.cov.save()
                if not self.args.quiet_coverage:
                    self.stream.coverage_percent = None
                    self.args.cov.report(file=self.stream,
                                         omit=self.args.omit_patterns,
                                         show_missing=True)
                    self.coverage_percent = self.stream.coverage_percent

            except CoverageException as ce:
                if (len(ce.args) == 1) and ("No data to report" not in ce.args[0]):
                    raise ce

        if self.testsRun and not self.shouldStop:
            self.stream.writeln()
        if self.shouldStop:
            self.stream.writeln()
            self.stream.writeln(self.colors.yellow(
                "Warning: Some tests may not have been run."))
            self.stream.writeln()
        self.stream.writeln("Ran %s test%s in %ss using %s process%s" %
                            (self.colors.bold(str(self.testsRun)),
                             self.testsRun != 1 and "s" or "",
                             self.colors.bold("%.3f" % self.timeTaken),
                             self.colors.bold("%d" % self.args.processes),
                             self.args.processes != 1 and "es" or ""))
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
                stats.append("{}={}".format(name,
                                            color_func(str(len(obj_list)))))
        if not stats:
            self.stream.writeln(self.colors.failing("No Tests Found"))
        else:
            grade = self.colors.passing('OK')
            if self.errors or self.failures:
                grade = self.colors.failing('FAILED')
            self.stream.writeln("{} ({})".format(grade, ', '.join(stats)))

    def startTest(self, test):
        """
        Called before the start of each test
        """
        # Get our bearings
        test = proto_test(test)
        current_module = test.module
        current_class  = test.class_name

        # Output
        if self.showAll:
            # Module...if it changed.
            if current_module != self.last_module:
                self.stream.writeln(self.colors.moduleName(current_module))
            # Class...if it changed.
            if current_class != self.last_class:
                self.stream.writeln(self.colors.className(
                    self.stream.formatText(current_class, indent=1)))
            if self.stream.isatty():
                # In the terminal, we will write a placeholder, and then
                # modify the first character and rewrite it in color after
                # the test has run.
                self.first_text_output = self.stream.formatLine(
                    test.getDescription(self.verbose),
                    indent=2)
                self.stream.write(self.colors.bold(self.first_text_output))
            self.stream.flush()

        # Set state for next time
        if current_module != self.last_module:
            self.last_module = current_module
        if current_class != self.last_class:
            self.last_class = current_class

    def stopTest(self, test):
        """
        Supposed to be called after each test, but as far as I can tell that's a
        lie and this is simply never called.
        """


    def _reportOutcome(self, test, outcome_char, color_func, err=None,
                       reason=''):
        self.testsRun += 1
        test = proto_test(test)
        if self.showAll:
            if self.stream.isatty():
                self.stream.write(self.colors.start_of_line())
            # Can end up being different from the first time due to subtest
            # information only being available after a test result comes in.
            second_text_output = self.stream.formatLine(
                test.getDescription(self.verbose),
                indent=2,
                outcome_char=outcome_char)
            if terminal_width: # pragma: no cover
                cursor_rewind = int(ceil(float(len(self.first_text_output)) / terminal_width)) - 1
                if cursor_rewind:
                    self.stream.write(self.colors.up(cursor_rewind))
            self.stream.write(color_func(second_text_output))
            if reason:
                self.stream.write(color_func(' -- ' + reason))
            self.stream.writeln()
            self.stream.flush()
        elif self.dots:
            self.stream.write(color_func(outcome_char))
            self.stream.flush()

    def addSuccess(self, test):
        """
        Called when a test passed
        """
        test = proto_test(test)
        self.passing.append(test)
        self._reportOutcome(test, '.', self.colors.passing)

    @failfast
    def addError(self, test, err):
        """
        Called when a test raises an exception
        """
        test = proto_test(test)
        err = proto_error(err)
        self.errors.append((test, err))
        self.all_errors.append((test, self.colors.error, 'Error', err))
        self._reportOutcome(test, 'E', self.colors.error, err)

    @failfast
    def addFailure(self, test, err):
        """
        Called when a test fails a unittest assertion
        """
        # Special case: Catch Twisted's skips that come thtrough as failures
        # and treat them as skips instead
        if len(err.traceback_lines) == 1:
            if err.traceback_lines[0].startswith('UnsupportedTrialFeature'):
                reason = eval(err.traceback_lines[0][25:])[1]
                self.addSkip(test, reason)
                return

        test = proto_test(test)
        err = proto_error(err)
        self.failures.append((test, err))
        self.all_errors.append((test, self.colors.error, 'Failure', err))
        self._reportOutcome(test, 'F', self.colors.failing, err)

    def addSkip(self, test, reason):
        """
        Called when a test is skipped
        """
        test = proto_test(test)
        self.skipped.append((test, reason))
        self._reportOutcome(
                test, 's', self.colors.skipped, reason=reason)

    def addExpectedFailure(self, test, err):
        """
        Called when a test fails, and we expeced the failure
        """
        test = proto_test(test)
        err = proto_error(err)
        self.expectedFailures.append((test, err))
        self._reportOutcome(test, 'x', self.colors.expectedFailure, err)

    def addUnexpectedSuccess(self, test):
        """
        Called when a test passed, but we expected a failure
        """
        test = proto_test(test)
        self.unexpectedSuccesses.append(test)
        self._reportOutcome(test, 'u', self.colors.unexpectedSuccess)

    def printErrors(self):
        """
        Print a list of all tracebacks from errors and failures, as well as
        captured stdout (even if the test passed, except with quiet_stdout
        option).
        """
        if self.dots:
            self.stream.writeln()

        # Skipped Test Report
        if not self.args.no_skip_report:
            for test, reason in self.skipped:
                self.stream.writeln("\n{} {} - {}".format(
                    self.colors.blue('Skipped'),
                    self.colors.bold(test.dotted_name),
                    reason))

        # Captured output for non-failing tests
        if not self.args.quiet_stdout:
            failing_tests = set([x[0] for x in self.all_errors])
            for test in list(self.stdout_output):
                if test not in failing_tests:
                    self.displayStdout(test)
                    self.displayStderr(test)

        # Actual tracebacks and captured output for failing tests
        for (test, color_func, outcome, err) in self.all_errors:
            # Header Line
            self.stream.writeln(
                    '\n' + color_func(outcome) +
                    ' in ' + self.colors.bold(test.dotted_name))

            # Traceback
            if not self.args.no_tracebacks:
                relevant_frames = []
                for i, frame in enumerate(err.traceback_lines):
                    # Python2 tracebacks containing unicode need some special handling
                    # This doesn't always make it readable, but at least it doesn't
                    # crash
                    if sys.version_info[0] == 2: # pragma: no cover
                        try:
                            ''.join([frame]) # intentionally trigger exceptions
                        except UnicodeDecodeError:
                            frame = frame.decode('utf-8')
                    debug('\n' + '*' * 30 + "Frame {}:".format(i) + '*' * 30
                          + "\n{}".format(self.colors.yellow(frame)), level=3)
                    # Ignore useless frames
                    if self.verbose < 4:
                        if frame.strip() == "Traceback (most recent call last):":
                            continue
                    # Done with this frame, capture it.
                    relevant_frames.append(frame)
                self.stream.write(''.join(relevant_frames))

            # Captured output for failing tests
            self.displayStdout(test)
            self.displayStderr(test)

    def wasSuccessful(self):
        """
        Tells whether or not the overall run was successful
        """
        if self.args.minimum_coverage != None:
            if self.coverage_percent < self.args.minimum_coverage:
                self.stream.writeln(self.colors.red(
                    "Coverage of {}% is below minimum level of {}%"
                    .format(self.coverage_percent, self.args.minimum_coverage)))
                return False

        # fail if no tests are run.
        if sum(len(x) for x in [
                self.errors,
                self.expectedFailures,
                self.failures,
                self.passing,
                self.skipped,
                self.unexpectedSuccesses]) == 0:
            return False
        else:
            return len(self.all_errors) == 0
