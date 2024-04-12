"""Classes and methods to handle test results."""

from __future__ import annotations

import argparse
from doctest import DocTest, DocTestCase
from math import ceil
from shutil import get_terminal_size
import time
import traceback
from typing import Any, Callable, Sequence, TYPE_CHECKING, Union
from unittest.result import failfast
from unittest import TestCase, TestSuite

from green.output import Colors, debug, GreenStream
from green.version import pretty_version

if TYPE_CHECKING:
    from green.process import ExcInfoType

    TestCaseT = Union["ProtoTest", TestCase, DocTestCase]
    RunnableTestT = Union[TestCaseT, TestSuite]

terminal_width, _ignored = get_terminal_size()


def proto_test(test: RunnableTestT) -> ProtoTest:
    """
    If test is a ProtoTest, I just return it.
    Otherwise, I create a ProtoTest out of test and return it.
    """
    if isinstance(test, ProtoTest):
        return test
    return ProtoTest(test)


def proto_error(err: ExcInfoType | ProtoError) -> ProtoError:
    """
    If err is a ProtoError, I just return it.
    Otherwise, I create a ProtoError out of err and return it.
    """
    if isinstance(err, ProtoError):
        return err
    return ProtoError(err)


class ProtoTest:
    """
    I take a full-fledged TestCase and preserve just the information we need
    and can pass between processes.
    """

    module: str = ""
    class_name: str = ""
    method_name: str = ""
    docstr_part: str = ""
    subtest_part: str = ""
    test_time: str = "0.0"
    failureException = AssertionError
    description: str = ""

    # Doctests specific attributes:
    is_doctest: bool = False
    filename: str | None = None
    name: str = ""

    def __init__(self, test: TestCase | DocTestCase | TestSuite | None = None) -> None:
        # Teardown handling is a royal mess
        self.is_class_or_module_teardown_error: bool = False

        # Is this a subtest? The _SubTest class is private so we need to check the attributes.
        sub_description = getattr(test, "_subDescription", None)
        if sub_description is not None:
            self.subtest_part = " " + sub_description()
            test = test.test_case  # type: ignore

        # Is this a DocTest?
        # We need to know that this is a doctest, because doctests are very
        # different than regular test cases in many ways, so they get special
        # treatment inside and outside of this class.
        if isinstance(test, DocTestCase):
            self.is_doctest = True
            dt_test: DocTest = test._dt_test  # type: ignore
            self.name = dt_test.name
            # We had to inject this in green/loader.py -- this is the test
            # module that specified that we should load doctests from some
            # other module -- so that we'll group the doctests with the test
            # module that specified that we should load them.
            self.module = test.__module__
            self.class_name = "DocTests via `doctest_modules = [...]`"
            # I'm not sure this will be the correct way to get the method name
            # in all cases.
            self.method_name = self.name.split(".")[1]
            self.filename = dt_test.filename
            self.lineno = dt_test.lineno

        # Is this a TestCase?
        elif isinstance(test, TestCase):
            self.module = test.__module__
            self.class_name = test.__class__.__name__
            self.method_name = str(test).split()[0]
            # docstr_part strips initial whitespace, then combines all lines
            # into one string until the first completely blank line in the
            # docstring
            doc_segments = []
            if getattr(test, "_testMethodDoc", None):
                for line in test._testMethodDoc.lstrip().split("\n"):
                    line = line.strip()
                    if not line:
                        break
                    doc_segments.append(line)
            self.docstr_part = " ".join(doc_segments)

    def __eq__(self, other: Any) -> bool:
        return self.__hash__() == other.__hash__()

    def __hash__(self) -> int:
        return hash(self.dotted_name)

    def __str__(self) -> str:
        return self.dotted_name

    @property
    def dotted_name(self, ignored: Any = None) -> str:
        if self.is_doctest or self.is_class_or_module_teardown_error:
            return self.name
        return f"{self.module}.{self.class_name}.{self.method_name}{self.subtest_part}"

    def getDescription(self, verbose: int) -> str:
        # Classes or module teardown errors
        if self.is_class_or_module_teardown_error:
            return self.name
        # Doctests
        if self.is_doctest:
            if verbose == 2:
                return self.name
            if verbose > 2:
                return f"{self.name} -> {self.filename}:{self.lineno}"
            return ""
        # Regular tests
        if verbose == 2:
            return f"{self.method_name}{self.subtest_part}"
        elif verbose == 3:
            return f"{self.docstr_part}{self.subtest_part}" or self.method_name
        elif verbose > 3:
            if self.docstr_part + self.subtest_part:
                return f"{self.method_name}: {self.docstr_part}{self.subtest_part}"
            return self.method_name
        return ""


class ProtoError:
    """
    I take a full-fledged test error and preserve just the information we need
    and can pass between processes.
    """

    def __init__(self, err: ExcInfoType) -> None:
        self.traceback_lines = traceback.format_exception(*err)

    def __str__(self) -> str:
        return "\n".join(self.traceback_lines)


class BaseTestResult:
    """
    I am inherited by ProtoTestResult and GreenTestResult.
    """

    def __init__(self, stream: GreenStream | None, *, colors: Colors | None = None):
        self.stdout_output: dict[ProtoTest, str] = {}
        self.stderr_errput: dict[ProtoTest, str] = {}
        self.stream: GreenStream | None = stream
        self.colors: Colors = colors or Colors()
        # The collectedDurations list is new in Python 3.12.
        self.collectedDurations: list[tuple[str, float]] = []

    def recordStdout(self, test: RunnableTestT, output):
        """
        Called with stdout that the suite decided to capture so we can report
        the captured output somewhere.
        """
        if output:
            test = proto_test(test)
            self.stdout_output[test] = output

    def recordStderr(self, test: RunnableTestT, errput):
        """
        Called with stderr that the suite decided to capture so we can report
        the captured "errput" somewhere.
        """
        if errput:
            test = proto_test(test)
            self.stderr_errput[test] = errput

    def displayStdout(self, test: TestCaseT):
        """
        Displays AND REMOVES the output captured from a specific test.  The
        removal is done so that this method can be called multiple times
        without duplicating results output.
        """
        test = proto_test(test)
        if test.dotted_name in self.stdout_output:
            if self.stream is None:
                raise ValueError("stream is None")
            colors = self.colors
            captured = "Captured stdout"
            self.stream.write(
                f"\n{colors.yellow(captured)} for {colors.bold(test.dotted_name)}\n"
                f"{self.stdout_output[test]}"
            )
            del self.stdout_output[test]

    def displayStderr(self, test: TestCaseT):
        """
        Displays AND REMOVES the errput captured from a specific test.  The
        removal is done so that this method can be called multiple times
        without duplicating results errput.
        """
        test = proto_test(test)
        if test.dotted_name in self.stderr_errput:
            if self.stream is None:
                raise ValueError("stream is None")
            colors = self.colors
            captured = "Captured stderr"
            self.stream.write(
                f"\n{colors.yellow(captured)} for {colors.bold(test.dotted_name)}\n"
                f"{self.stderr_errput[test]}"
            )
            del self.stderr_errput[test]

    def addDuration(self, test: TestCaseT, elapsed: float):
        """
        Called when a test finished running, regardless of its outcome.

        New in Python 3.12.

        Args:
            test: The test case corresponding to the test method.
            elapsed: The time represented in seconds, including the
                execution of cleanup functions.
        """
        self.collectedDurations.append((str(test), elapsed))


class ProtoTestResult(BaseTestResult):
    """
    I'm the TestResult object for a single unit test run in a process.
    """

    failfast: bool = False  # Because unittest inspects the attribute
    finalize_callback_called: bool = False
    shouldStop: bool = False
    start_time: float = 0.0
    test_time: str = ""

    def __init__(
        self,
        start_callback: Callable[[RunnableTestT], None] | None = None,
        finalize_callback: Callable[[ProtoTestResult], None] | None = None,
    ) -> None:
        super().__init__(None, colors=None)
        self.start_callback = start_callback
        self.finalize_callback = finalize_callback
        self.collectedDurations: list[tuple[str, float]] = []
        self.errors: list[tuple[ProtoTest, ProtoError]] = []
        self.expectedFailures: list[tuple[ProtoTest, ProtoError]] = []
        self.failures: list[tuple[ProtoTest, ProtoError]] = []
        self.passing: list[ProtoTest] = []
        self.skipped: list[tuple[ProtoTest, str]] = []
        self.unexpectedSuccesses: list[ProtoTest] = []
        self.pickle_attrs: Sequence[str] = (
            "errors",
            "expectedFailures",
            "failures",
            "passing",
            "pickle_attrs",  # TODO: check if pickle_attrs should be pickled.
            "shouldStop",
            "skipped",
            "stderr_errput",
            "stdout_output",
            "test_time",
            "unexpectedSuccesses",
        )
        self.reinitialize()

    def reinitialize(self):
        self.shouldStop = False
        self.collectedDurations.clear()
        self.errors.clear()
        self.expectedFailures.clear()
        self.failures.clear()
        self.passing.clear()
        self.skipped.clear()
        self.unexpectedSuccesses.clear()
        self.start_time = 0.0
        self.test_time = ""

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"errors{self.errors},"
            f" expectedFailures{self.expectedFailures},"
            f" failures{self.failures},"
            f" passing{self.passing},"
            f" skipped{self.skipped},"
            f" unexpectedSuccesses{self.unexpectedSuccesses},"
            f" test_time{self.test_time}"
        )

    def __getstate__(self) -> dict[str, Any]:
        """
        Prevent the callback functions from getting pickled.
        """
        result_dict = {}
        for pickle_attr in self.pickle_attrs:
            result_dict[pickle_attr] = self.__dict__[pickle_attr]
        return result_dict

    def __setstate__(self, state: dict[str, Any]) -> None:
        """
        Since the callback functions weren't pickled, we need to initialize them.
        """
        self.__dict__.update(state)
        self.start_callback = None
        self.finalize_callback = None

    def startTest(self, test: RunnableTestT) -> None:
        """
        Called before each test runs.
        """
        test = proto_test(test)
        self.reinitialize()
        self.start_time = time.time()
        if self.start_callback:
            self.start_callback(test)

    def stopTest(self, test: RunnableTestT) -> None:
        """
        Called after each test runs.
        """
        if self.start_time:
            self.test_time = str(time.time() - self.start_time)
        else:
            self.test_time = "0.0"

    def finalize(self) -> None:
        """
        I am here so that after the GreenTestSuite has had a chance to inject
        the captured stdout/stderr back into me, I can relay that through to
        the worker process's poolRunner who will send me back up to the parent
        process.
        """
        if self.finalize_callback:
            self.finalize_callback(self)
            self.finalize_callback_called = True

    def addSuccess(self, test: TestCaseT) -> None:
        """
        Called when a test passed.
        """
        self.passing.append(proto_test(test))

    def addError(self, test: RunnableTestT, err: ProtoError | ExcInfoType) -> None:
        """
        Called when a test raises an exception.
        """
        self.errors.append((proto_test(test), proto_error(err)))

    def addFailure(self, test: TestCaseT, err: ExcInfoType) -> None:
        """
        Called when a test fails a unittest assertion.
        """
        self.failures.append((proto_test(test), proto_error(err)))

    def addSkip(self, test: TestCaseT, reason: str) -> None:
        """
        Called when a test is skipped.
        """
        self.skipped.append((proto_test(test), reason))

    def addExpectedFailure(self, test: TestCaseT, err: ExcInfoType) -> None:
        """
        Called when a test fails, and we expected the failure.
        """
        self.expectedFailures.append((proto_test(test), proto_error(err)))

    def addUnexpectedSuccess(self, test: TestCaseT) -> None:
        """
        Called when a test passed, but we expected a failure
        """
        self.unexpectedSuccesses.append(proto_test(test))

    # The _SubTest class is private and masked so we cannot easily type annotate.
    def addSubTest(
        self, test: TestCaseT, subtest: Any, err: ExcInfoType | None
    ) -> None:
        """
        Called at the end of a subtest no matter its result.

        The test that runs the subtests calls the other test methods to
        record its own result.  We use this method to record each subtest as a
        separate test result.  It's very meta.
        """
        if err is not None:
            if err[0] is not None and issubclass(err[0], test.failureException):
                self.addFailure(subtest, err)
            else:
                self.addError(subtest, err)


class GreenTestResult(BaseTestResult):
    """
    Aggregates test results and outputs them to a stream.
    """

    stream: GreenStream
    last_class: str = ""
    last_module: str = ""
    first_text_output: str = ""
    shouldStop: bool = False

    def __init__(self, args: argparse.Namespace, stream: GreenStream) -> None:
        super().__init__(stream, colors=Colors(args.termcolor))
        self.args = args
        self.showAll: bool = args.verbose > 1
        self.dots: bool = args.verbose == 1
        self.verbose: int = args.verbose
        self.failfast = args.failfast
        self.testsRun: int = 0
        # Individual lists
        self.collectedDurations: list[tuple[str, float]] = []
        self.errors: list[tuple[ProtoTest, ProtoError]] = []
        self.expectedFailures: list[tuple[ProtoTest, ProtoError]] = []
        self.failures: list[tuple[ProtoTest, ProtoError]] = []
        self.passing: list[ProtoTest] = []
        self.skipped: list[tuple[ProtoTest, str]] = []
        self.unexpectedSuccesses: list[ProtoTest] = []
        # Combination of all errors and failures
        self.all_errors: list[
            tuple[ProtoTest, Callable[[str], str], str, ProtoError]
        ] = []
        # For exiting non-zero if we don't reach a certain level of coverage
        self.coverage_percent: int | None = None

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"tests run: {self.testsRun}, "
            f"errors{self.errors}, "
            f"expectedFailures{self.expectedFailures}, "
            f"failures{self.failures}, "
            f"passing{self.passing}, "
            f"skipped{self.skipped}, "
            f"unexpectedSuccesses{self.unexpectedSuccesses}"
        )

    def stop(self) -> None:
        self.shouldStop = True

    def tryRecordingStdoutStderr(
        self,
        test: ProtoTest,
        proto_test_result: ProtoTestResult,
        err: ProtoError | None = None,
    ) -> None:
        if proto_test_result.stdout_output.get(test, False):
            self.recordStdout(test, proto_test_result.stdout_output[test])
        if proto_test_result.stderr_errput.get(test, False):
            self.recordStderr(test, proto_test_result.stderr_errput[test])

        # SubTest errors/failures (but not successes) generate a different err object, so we have to
        # do some inspection to figure out which object has the output/errput
        if (test.class_name == "SubTest") and err:
            for t in proto_test_result.stdout_output.keys():
                if test.dotted_name.startswith(t.dotted_name):
                    self.recordStdout(test, proto_test_result.stdout_output[t])
                    break
            for t in proto_test_result.stderr_errput.keys():
                if test.dotted_name.startswith(t.dotted_name):
                    self.recordStderr(test, proto_test_result.stderr_errput[t])
                    break

    def addProtoTestResult(self, proto_test_result: ProtoTestResult) -> None:
        for test, err in proto_test_result.errors:
            self.addError(test, err, proto_test_result.test_time)
            self.tryRecordingStdoutStderr(test, proto_test_result, err)
        for test, err in proto_test_result.expectedFailures:
            self.addExpectedFailure(test, err, proto_test_result.test_time)
            self.tryRecordingStdoutStderr(test, proto_test_result, err)
        for test, err in proto_test_result.failures:
            self.addFailure(test, err, proto_test_result.test_time)
            self.tryRecordingStdoutStderr(test, proto_test_result, err)
        for test in proto_test_result.passing:
            self.addSuccess(test, proto_test_result.test_time)
            self.tryRecordingStdoutStderr(test, proto_test_result)
        for test, reason in proto_test_result.skipped:
            self.addSkip(test, reason, proto_test_result.test_time)
            self.tryRecordingStdoutStderr(test, proto_test_result)
        for test in proto_test_result.unexpectedSuccesses:
            self.addUnexpectedSuccess(test, proto_test_result.test_time)
            self.tryRecordingStdoutStderr(test, proto_test_result)

    def startTestRun(self) -> None:
        """
        Called once before any tests run.
        """
        self.startTime = time.time()
        # Really verbose information
        if self.verbose > 2:
            self.stream.writeln(self.colors.bold(f"{pretty_version()}\n"))

    def stopTestRun(self) -> None:
        """
        Called once after all tests have run.
        """
        # FIXME: stopTime and timeTaken are defined outside __init__.
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
                    self.args.cov.report(
                        file=self.stream,
                        omit=self.args.omit_patterns,
                        show_missing=True,
                        ignore_errors=True,
                    )
                    self.coverage_percent = self.stream.coverage_percent

            except CoverageException as ce:
                if (len(ce.args) == 1) and ("No data to report" not in ce.args[0]):
                    raise ce

        if self.testsRun and not self.shouldStop:
            self.stream.writeln()
        if self.shouldStop:
            self.stream.writeln()
            self.stream.writeln(
                self.colors.yellow("Warning: Some tests may not have been run.")
            )
            self.stream.writeln()
        self.stream.writeln(
            "Ran %s test%s in %ss using %s process%s"
            % (
                self.colors.bold(str(self.testsRun)),
                self.testsRun != 1 and "s" or "",
                self.colors.bold("%.3f" % self.timeTaken),
                self.colors.bold("%d" % self.args.processes),
                self.args.processes != 1 and "es" or "",
            )
        )
        self.stream.writeln()
        results: tuple[tuple[list, str, Callable[[str], str]], ...] = (
            (self.errors, "errors", self.colors.error),
            (self.expectedFailures, "expected_failures", self.colors.expectedFailure),
            (self.failures, "failures", self.colors.failing),
            (self.passing, "passes", self.colors.passing),
            (self.skipped, "skips", self.colors.skipped),
            (
                self.unexpectedSuccesses,
                "unexpected_successes",
                self.colors.unexpectedSuccess,
            ),
        )
        stats = []
        for obj_list, name, color_func in results:
            if obj_list:
                stats.append(f"{name}={color_func(str(len(obj_list)))}")
        if not stats:
            self.stream.writeln(self.colors.failing("No Tests Found"))
        else:
            grade = self.colors.passing("OK")
            if not self.wasSuccessful():
                grade = self.colors.failing("FAILED")
            self.stream.writeln(f"{grade} ({', '.join(stats)})")

    def startTest(self, test: RunnableTestT) -> None:
        """
        Called before the start of each test.
        """
        # Get our bearings
        test = proto_test(test)
        current_module = test.module
        current_class = test.class_name

        # Output
        if self.showAll:
            # Module...if it changed.
            if current_module != self.last_module:
                self.stream.writeln(self.colors.moduleName(current_module))
            # Class...if it changed.
            if current_class != self.last_class:
                self.stream.writeln(
                    self.colors.className(
                        self.stream.formatText(current_class, indent=1)
                    )
                )
            if self.stream.isatty():
                # In the terminal, we will write a placeholder, and then
                # modify the first character and rewrite it in color after
                # the test has run.
                self.first_text_output = self.stream.formatLine(
                    test.getDescription(self.verbose), indent=2
                )
                self.stream.write(self.colors.bold(self.first_text_output))
            self.stream.flush()

        # Set state for next time
        if current_module != self.last_module:
            self.last_module = current_module
        if current_class != self.last_class:
            self.last_class = current_class

    def stopTest(self, test: RunnableTestT) -> None:
        """
        Supposed to be called after each test.
        """

    def _reportOutcome(
        self,
        test: RunnableTestT,
        outcome_char: str,
        color_func: Callable[[str], str],
        err: ProtoError | None = None,
        reason: str = "",
    ) -> None:
        self.testsRun += 1
        test = proto_test(test)
        if self.showAll:
            if self.stream.isatty():
                self.stream.write(self.colors.start_of_line())
            # Can end up being different from the first time due to subtest
            # information only being available after a test result comes in.
            second_text_output = self.stream.formatLine(
                test.getDescription(self.verbose), indent=2, outcome_char=outcome_char
            )
            if self.stream.isatty() and terminal_width:  # pragma: no cover
                cursor_rewind = (
                    int(ceil(len(self.first_text_output) / terminal_width)) - 1
                )
                if cursor_rewind:
                    self.stream.write(self.colors.up(cursor_rewind))
            self.stream.write(color_func(second_text_output))
            if reason:
                self.stream.write(color_func(" -- " + reason))
            self.stream.writeln()
            self.stream.flush()
        elif self.dots:
            self.stream.write(color_func(outcome_char))
            self.stream.flush()

    def addSuccess(
        self, test: RunnableTestT, test_time: float | str | None = None
    ) -> None:
        """
        Called when a test passed.
        """
        test = proto_test(test)
        if test_time:
            test.test_time = str(test_time)
        self.passing.append(test)
        self._reportOutcome(test, ".", self.colors.passing)

    @failfast
    def addError(
        self, test: RunnableTestT, err: ProtoError, test_time: float | str | None = None
    ) -> None:
        """
        Called when a test raises an exception.
        """
        test = proto_test(test)
        if test_time:
            test.test_time = str(test_time)
        error = proto_error(err)
        self.errors.append((test, error))
        self.all_errors.append((test, self.colors.error, "Error", error))
        self._reportOutcome(test, "E", self.colors.error, error)

    @failfast
    def addFailure(
        self, test: RunnableTestT, err: ProtoError, test_time: float | str | None = None
    ) -> None:
        """
        Called when a test fails a unittest assertion.
        """
        # Special case: Catch Twisted's skips that come thtrough as failures
        # and treat them as skips instead
        if len(err.traceback_lines) == 1:
            if err.traceback_lines[0].startswith("UnsupportedTrialFeature"):
                reason = eval(err.traceback_lines[0][25:])[1]
                self.addSkip(test, reason)
                return

        test_proto = proto_test(test)
        if test_time:
            test_proto.test_time = str(test_time)
        self.failures.append((test_proto, err))
        self.all_errors.append((test_proto, self.colors.error, "Failure", err))
        self._reportOutcome(test_proto, "F", self.colors.failing, err)

    def addSkip(
        self, test: RunnableTestT, reason: str, test_time: float | str | None = None
    ) -> None:
        """
        Called when a test is skipped.
        """
        test = proto_test(test)
        if test_time:
            test.test_time = str(test_time)
        self.skipped.append((test, reason))
        self._reportOutcome(test, "s", self.colors.skipped, reason=reason)

    def addExpectedFailure(
        self, test: RunnableTestT, err: ProtoError, test_time: float | str | None = None
    ) -> None:
        """
        Called when a test fails, and we expected the failure.
        """
        test = proto_test(test)
        if test_time:
            test.test_time = str(test_time)
        err = proto_error(err)
        self.expectedFailures.append((test, err))
        self._reportOutcome(test, "x", self.colors.expectedFailure, err)

    def addUnexpectedSuccess(
        self, test: RunnableTestT, test_time: float | str | None = None
    ) -> None:
        """
        Called when a test passed, but we expected a failure.
        """
        test = proto_test(test)
        if test_time:
            test.test_time = str(test_time)
        self.unexpectedSuccesses.append(test)
        self._reportOutcome(test, "u", self.colors.unexpectedSuccess)

    def printErrors(self) -> None:
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
                self.stream.writeln(
                    "\n{} {} - {}".format(
                        self.colors.blue("Skipped"),
                        self.colors.bold(test.dotted_name),
                        reason,
                    )
                )

        # Captured output for non-failing tests
        if not self.args.quiet_stdout:
            failing_tests = {x[0] for x in self.all_errors}
            for test in list(self.stdout_output) + list(self.stderr_errput):
                if test not in failing_tests:
                    self.displayStdout(test)
                    self.displayStderr(test)

        # Actual tracebacks and captured output for failing tests
        for test, color_func, outcome, err in self.all_errors:
            # Header Line
            self.stream.writeln(
                f"\n{color_func(outcome)} in {self.colors.bold(test.dotted_name)}"
            )

            # Traceback
            if not self.args.no_tracebacks:
                relevant_frames = []
                for i, frame in enumerate(err.traceback_lines):
                    debug(
                        "\n"
                        f"{'*' * 30}Frame {i}:{'*' * 30}\n" + self.colors.yellow(frame),
                        level=3,
                    )
                    # Ignore useless frames
                    if self.verbose < 4:
                        if frame.strip() == "Traceback (most recent call last):":
                            continue
                    # Done with this frame, capture it.
                    relevant_frames.append(frame)
                self.stream.write("".join(relevant_frames))

            # Captured output for failing tests
            self.displayStdout(test)
            self.displayStderr(test)

    def wasSuccessful(self) -> bool:
        """
        Tells whether or not the overall run was successful.
        """
        if self.args.minimum_coverage is not None:
            if self.coverage_percent < self.args.minimum_coverage:
                self.stream.writeln(
                    self.colors.red(
                        "Coverage of {}% is below minimum level of {}%".format(
                            self.coverage_percent, self.args.minimum_coverage
                        )
                    )
                )
                return False

        # fail if no tests are run.
        if not any(
            (
                self.errors,
                self.expectedFailures,
                self.failures,
                self.passing,
                self.skipped,
                self.unexpectedSuccesses,
            )
        ):
            return False
        return not self.all_errors and not self.unexpectedSuccesses
