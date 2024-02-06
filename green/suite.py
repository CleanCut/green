from __future__ import annotations

import argparse
from fnmatch import fnmatch
from io import StringIO
import sys
import unittest
from typing import Iterable, TYPE_CHECKING
from unittest.suite import _call_if_exists, _DebugResult, _isnotsuite, TestSuite  # type: ignore
from unittest import util

from green.config import get_default_args
from green.output import GreenStream

if TYPE_CHECKING:
    from unittest.case import TestCase
    from unittest.result import TestResult
    from green.result import GreenTestResult, ProtoTestResult


class GreenTestSuite(TestSuite):
    """
    This version of a test suite has two important functions:

    1) It brings Python 3.x-like features to Python 2.7
    2) It adds Green-specific features  (see customize())
    """

    args: argparse.Namespace | None = None

    def __init__(
        self,
        tests: Iterable[TestCase | TestSuite] = (),
        args: argparse.Namespace | None = None,
    ) -> None:
        # You should either set GreenTestSuite.args before instantiation, or
        # pass args into __init__
        self._removed_tests = 0
        default_args = get_default_args()
        self.allow_stdout = default_args.allow_stdout
        self.full_test_pattern = "test" + default_args.test_pattern
        self.customize(args)
        super().__init__(tests)

    def addTest(self, test: TestCase | TestSuite) -> None:
        """
        Override default behavior with some green-specific behavior.
        """
        if self.full_test_pattern:
            # test can actually be suites and things.  Only tests have _testMethodName.
            method_name = getattr(test, "_testMethodName", None)
            # Fake test cases (generated for module import failures, for example)
            # do not start with 'test'.  We still want to see those fake cases.
            if (
                method_name
                and method_name.startswith("test")
                and not fnmatch(method_name, self.full_test_pattern)
            ):
                return
        super().addTest(test)

    def customize(self, args: argparse.Namespace | None) -> None:
        """
        Green-specific behavior customization via an args dictionary from
        the green.config module.  If you don't pass in an args dictionary,
        then this class acts like TestSuite from Python 3.x.
        """
        # Set a new args on the CLASS
        if args:
            self.args = args

        # Use the class args
        if self.args and getattr(self.args, "allow_stdout", None):
            self.allow_stdout = self.args.allow_stdout
        if self.args and getattr(self.args, "test_pattern", None):
            self.full_test_pattern = "test" + self.args.test_pattern

    def _removeTestAtIndex(self, index: int) -> None:
        """
        Python 3.x-like version of this function for Python 2.7's sake.
        """
        test = self._tests[index]
        if hasattr(test, "countTestCases"):
            self._removed_tests += test.countTestCases()
        # FIXME: The upstream typing does not allow None:
        #  unittest.suite.BaseTestSuite._tests: list[unittest.case.TestCase]
        self._tests[index] = None  # type: ignore

    def countTestCases(self) -> int:
        """
        Python 3.x-like version of this function for Python 2.7's sake.
        """
        cases = self._removed_tests
        for test in self:
            if test:
                cases += test.countTestCases()
        return cases

    def _handleClassSetUp(
        self, test: TestCase | TestSuite, result: ProtoTestResult
    ) -> None:
        previousClass = getattr(result, "_previousTestClass", None)
        currentClass = test.__class__
        if currentClass == previousClass:
            return
        if result._moduleSetUpFailed:  # type: ignore[attr-defined]
            return
        if getattr(currentClass, "__unittest_skip__", False):
            return

        try:
            currentClass._classSetupFailed = False  # type: ignore
        except TypeError:
            # test may actually be a function
            # so its class will be a builtin-type
            pass

        setUpClass = getattr(currentClass, "setUpClass", None)
        if setUpClass is not None:
            _call_if_exists(result, "_setupStdout")
            try:
                setUpClass()
            # Upstream Python forgets to take SkipTest into account
            except unittest.case.SkipTest as e:
                currentClass.__unittest_skip__ = True  # type: ignore
                currentClass.__unittest_skip_why__ = str(e)  # type: ignore
            # -- END of fix
            except Exception as e:
                if isinstance(result, _DebugResult):
                    raise
                currentClass._classSetupFailed = True  # type: ignore
                className = util.strclass(currentClass)
                self._createClassOrModuleLevelException(  # type: ignore
                    result, e, "setUpClass", className
                )
            finally:
                _call_if_exists(result, "_restoreStdout")
                if currentClass._classSetupFailed is True:  # type: ignore
                    currentClass.doClassCleanups()  # type: ignore
                    if currentClass.tearDown_exceptions:  # type: ignore
                        for exc in currentClass.tearDown_exceptions:  # type: ignore
                            self._createClassOrModuleLevelException(  # type: ignore
                                result, exc[1], "setUpClass", className, info=exc
                            )

    def run(  # type: ignore[override]
        self, result: ProtoTestResult, debug: bool = False
    ) -> ProtoTestResult:
        """
        Emulate unittest's behavior, with Green-specific changes.
        """
        topLevel = False
        if getattr(result, "_testRunEntered", False) is False:
            result._testRunEntered = topLevel = True  # type: ignore

        for index, test in enumerate(self):
            if result.shouldStop:
                break

            if _isnotsuite(test):
                self._tearDownPreviousClass(test, result)  # type: ignore[attr-defined]
                self._handleModuleFixture(test, result)  # type: ignore[attr-defined]
                self._handleClassSetUp(test, result)  # type: ignore[attr-defined]
                result._previousTestClass = test.__class__  # type: ignore[attr-defined]

                if getattr(test.__class__, "_classSetupFailed", False) or getattr(
                    result, "_moduleSetUpFailed", False
                ):
                    continue

                if not self.allow_stdout:
                    captured_stdout = StringIO()
                    captured_stderr = StringIO()
                    saved_stdout = sys.stdout
                    saved_stderr = sys.stderr
                    sys.stdout = GreenStream(captured_stdout)  # type: ignore[assignment]
                    sys.stderr = GreenStream(captured_stderr)  # type: ignore[assignment]

            test(result)  # type: ignore[arg-type]

            if _isnotsuite(test):
                if not self.allow_stdout:
                    sys.stdout = saved_stdout
                    sys.stderr = saved_stderr
                    result.recordStdout(test, captured_stdout.getvalue())
                    result.recordStderr(test, captured_stderr.getvalue())
                # Since we're intercepting the stdout/stderr out here at the
                # suite level, we need to poke the test result and let it know
                # when we're ready to transmit results back up to the parent
                # process.  I would rather just do it automatically at test
                # stop time, but we don't have the captured stuff at that
                # point.  Messy...but the only other alternative I can think of
                # is monkey-patching loaded TestCases -- which could be from
                # unittest or twisted or some other custom subclass.
                result.finalize()

            self._removeTestAtIndex(index)

        # Green's subprocesses have handled all actual tests and sent up the
        # result, but unittest expects to be able to add teardown errors to
        # the result still, so we'll need to watch for that ourself.
        errors_before = len(result.errors)

        if topLevel:
            self._tearDownPreviousClass(None, result)  # type: ignore[attr-defined]
            self._handleModuleTearDown(result)  # type: ignore[attr-defined]
            result._testRunEntered = False  # type: ignore[attr-defined]

        # Special handling for class/module tear-down errors. startTest() and
        # finalize() both trigger communication between the subprocess and
        # the runner process. addError()
        if errors_before != len(result.errors):
            difference = len(result.errors) - errors_before
            result.errors, new_errors = (
                result.errors[:-difference],
                result.errors[-difference:],
            )
            for test_proto, err in new_errors:
                # test = ProtoTest()
                previous_test_class = result._previousTestClass  # type: ignore[attr-defined]
                test_proto.module = previous_test_class.__module__
                test_proto.class_name = previous_test_class.__name__
                # test.method_name = 'some method name'
                test_proto.is_class_or_module_teardown_error = True
                test_proto.name = "Error in class or module teardown"
                # test.docstr_part = 'docstr part' # error_holder.description
                result.startTest(test_proto)
                result.addError(test_proto, err)
                result.stopTest(test_proto)
                result.finalize()
        return result
