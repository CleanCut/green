from __future__ import unicode_literals
from __future__ import print_function

from collections import OrderedDict
import time
import traceback
from unittest.result import failfast

from green.output import Colors, debug
from green.version import pretty_version

try: # pragma nocover
    import html
    escape = html.escape
except: # pragma nocover
    import cgi
    escape = cgi.escape


def proto_test(test):
    """If test is a ProtoTest, I just return it.  Otherwise I create a
    ProtoTest out of test and return it."""
    if isinstance(test, ProtoTest):
        return test
    else:
        return ProtoTest(test)


def proto_error(err):
    """If err is a ProtoError, I just return it.  Otherwise I create a
    ProtoError out of err and return it."""
    if isinstance(err, ProtoError):
        return err
    else:
        return ProtoError(err)



class ProtoTest():
    """I take a full-fledged TestCase and preserve just the information we need
    and can pass between subprocesses.
    """


    def __init__(self, test=None):
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
        else:
            self.module = ''
            self.class_name = ''
            self.method_name = ''
            self.docstr_part = ''

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return hash(self.dotted_name)

    @property
    def dotted_name(self, ignored=None):
        return self.module + '.' + self.class_name + '.' + self.method_name


    def getDescription(self, verbose):
        if verbose == 2:
            return self.method_name
        elif verbose > 2:
            return self.docstr_part or self.method_name
        else:
            return ''



class ProtoError():
    """I take a full-fledged test error and preserve just the information we
    need and can bass between subprocesses.
    """


    def __init__(self, err=None):
        self.traceback_lines = traceback.format_exception(*err)


class BaseTestResult(object): # Breaks subclasses in 2.7 not inheriting object
    """
    I am inherited by ProtoTestResult and GreenTestResult.
    """

    def __init__(self, stream, colors):
        self.stdout_output = OrderedDict()
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
                    self.colors.blue('Captured stdout'),
                    self.colors.bold(test.dotted_name),
                    self.stdout_output[test]))
            del(self.stdout_output[test])


class ProtoTestResult(BaseTestResult):
    """
    I'm the TestResult object for a single unit test run in a subprocess.
    """


    def __init__(self):
        super(ProtoTestResult, self).__init__(None, None)
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
        self.passing.append(proto_test(test))


    def addError(self, test, err):
        "Called when a test raises an exception"
        self.errors.append((proto_test(test), proto_error(err)))


    def addFailure(self, test, err):
        "Called when a test fails a unittest assertion"
        self.failures.append((proto_test(test), proto_error(err)))


    def addSkip(self, test, reason):
        "Called when a test is skipped"
        self.skipped.append((proto_test(test), reason))


    def addExpectedFailure(self, test, err):
        "Called when a test fails, and we expeced the failure"
        self.expectedFailures.append((proto_test(test), proto_error(err)))


    def addUnexpectedSuccess(self, test):
        "Called when a test passed, but we expected a failure"
        self.unexpectedSuccesses.append(proto_test(test))

    @property
    def any_errors(self, ignored=None):
        "True if anything failed due to an error"
        return self.errors > 0


class GreenTestResult(BaseTestResult):
    "Aggregates test results and outputs them to a stream."


    def __init__(self, args, stream):
        super(GreenTestResult, self).__init__(
                stream,
                Colors(args.termcolor, args.html))
        self.showAll       = args.verbose > 1
        self.dots          = args.verbose == 1
        self.verbose       = args.verbose
        self.last_module   = ''
        self.last_class    = ''
        self.failfast      = args.failfast
        self.shouldStop    = False
        self.testsRun      = 0
        # Individual lists
        self.errors              = []
        self.expectedFailures    = []
        self.failures            = []
        self.passing             = []
        self.skipped             = []
        self.unexpectedSuccesses = []
        # Combination of all errors and failures
        self.all_errors = []


    def stop(self):
        self.shouldStop = True


    def addProtoTestResult(self, protoTestResult):
        for test, err in protoTestResult.errors:
            self.addError(test, err)
        for test, err in protoTestResult.expectedFailures:
            self.addExpectedFailure(test, err)
        for test, err in protoTestResult.failures:
            self.addFailure(test, err)
        for test in protoTestResult.passing:
            self.addSuccess(test)
        for test, reason in protoTestResult.skipped:
            self.addSkip(test, reason)
        for test in protoTestResult.unexpectedSuccesses:
            self.addUnexpectedSuccess(test)


    def startTestRun(self):
        "Called once before any tests run"
        self.startTime = time.time()
        # Really verbose information
        if self.colors.html:
            self.stream.write(
                    '<div style="font-family: Monaco, \'Courier New\', monospace; color: rgb(170,170,170); background: rgb(0,0,0); padding: 14px;">')
        if self.verbose > 2:
            self.stream.writeln(self.colors.bold(pretty_version() + "\n"))


    def stopTestRun(self):
        "Called once after all tests have run"
        self.stopTime = time.time()
        self.timeTaken = self.stopTime - self.startTime
        self.printErrors()
        if self.testsRun and not self.shouldStop:
            self.stream.writeln()
        if self.shouldStop:
            self.stream.writeln()
            self.stream.writeln(self.colors.yellow(
                "Warning: Some tests may not have been run."))
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
            # Test name or description
            if not self.colors.html and self.stream.isatty():
                # In the terminal, we will write a placeholder, and then
                # rewrite it in color after the test has run.
                self.stream.write(
                    self.colors.bold(
                        self.stream.formatLine(
                            test.getDescription(self.verbose),
                            indent=2)))
            self.stream.flush()

        # Set state for next time
        if current_module != self.last_module:
            self.last_module = current_module
        if current_class != self.last_class:
            self.last_class = current_class


    def stopTest(self, test):
        "Called after the end of each test"


    def _reportOutcome(self, test, outcome_char, color_func, err=None,
            reason=''):
        test = proto_test(test)
        if self.showAll:
            # Move the cursor back to the start of the line in terminal mode
            if not self.colors.html and self.stream.isatty():
                self.stream.write('\r')
            # Escape the HTML that may be in the docstring
            test_description = test.getDescription(self.verbose)
            if self.colors.html:
                test_description = escape(test_description)
            self.stream.write(
                color_func(
                    self.stream.formatLine(
                        test_description,
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
        test = proto_test(test)
        self.passing.append(test)
        self._reportOutcome(test, '.', self.colors.passing)


    @failfast
    def addError(self, test, err):
        "Called when a test raises an exception"
        test = proto_test(test)
        err = proto_error(err)
        self.errors.append((test, err))
        self.all_errors.append((test, self.colors.error, 'Error', err))
        self._reportOutcome(test, 'E', self.colors.error, err)


    @failfast
    def addFailure(self, test, err):
        "Called when a test fails a unittest assertion"
        test = proto_test(test)
        err = proto_error(err)
        self.failures.append((test, err))
        self.all_errors.append((test, self.colors.error, 'Failure', err))
        self._reportOutcome(test, 'F', self.colors.failing, err)


    def addSkip(self, test, reason):
        test = proto_test(test)
        "Called when a test is skipped"
        self.skipped.append((test, reason))
        self._reportOutcome(
                test, 's', self.colors.skipped, reason=reason)


    def addExpectedFailure(self, test, err):
        "Called when a test fails, and we expeced the failure"
        test = proto_test(test)
        err = proto_error(err)
        self.expectedFailures.append((test, err))
        self._reportOutcome(test, 'x', self.colors.expectedFailure, err)


    @failfast
    def addUnexpectedSuccess(self, test):
        "Called when a test passed, but we expected a failure"
        test = proto_test(test)
        self.unexpectedSuccesses.append(test)
        self._reportOutcome(test, 'u', self.colors.unexpectedSuccess)


    def printErrors(self):
        """
        Print a list of all tracebacks from errors and failures, as well as
        captured stdout (even if the test passed).
        """
        if self.dots:
            self.stream.writeln()

        # Captured output for non-failing tests
        failing_tests = set([x[0] for x in self.all_errors])
        for test in list(self.stdout_output):
            if test not in failing_tests:
                self.displayStdout(test)

        # Actual tracebacks and captured output for failing tests
        for (test, color_func, outcome, err) in self.all_errors:
            # Header Line
            self.stream.writeln(
                    '\n' + color_func(outcome) +
                    ' in ' + self.colors.bold(test.dotted_name))

            # Frame Line
            relevant_frames = []
            for i, frame in enumerate(err.traceback_lines):
                debug('\n' + '*' * 30 + "Frame {}:".format(i) + '*' * 30
                      + "\n{}".format(self.colors.yellow(frame)), level = 3)
                # Ignore useless frames
                if self.verbose < 4:
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

            # Captured output for failing tests
            self.displayStdout(test)


    def wasSuccessful(self):
        "Tells whether or not the overall run was successful"
        return len(self.all_errors) == 0
