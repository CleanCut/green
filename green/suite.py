from __future__ import unicode_literals
from __future__ import print_function

from fnmatch import fnmatch
import sys
from unittest.suite import _call_if_exists, _DebugResult, _isnotsuite, TestSuite
from unittest import util
import unittest
from io import StringIO

from green.config import default_args
from green.output import GreenStream
from green.result import ProtoTest


class GreenTestSuite(TestSuite):
    """
    This version of a test suite has two important functions:

    1) It brings Python 3.x-like features to Python 2.7
    2) It adds Green-specific features  (see customize())
    """

    args = None

    def __init__(self, tests=(), args=None):
        # You should either set GreenTestSuite.args before instantiation, or
        # pass args into __init__
        self._removed_tests = 0
        self.allow_stdout = default_args.allow_stdout
        self.full_test_pattern = "test" + default_args.test_pattern
        self.customize(args)
        super(GreenTestSuite, self).__init__(tests)

    def addTest(self, test):
        """
        Override default behavior with some green-specific behavior.
        """
        if (
            self.full_test_pattern
            # test can actually be suites and things.  Only tests have
            # _testMethodName
            and getattr(test, "_testMethodName", False)
            # Fake test cases (generated for module import failures, for example)
            # do not start with 'test'.  We still want to see those fake cases.
            and test._testMethodName.startswith("test")
        ):
            if not fnmatch(test._testMethodName, self.full_test_pattern):
                return
        super(GreenTestSuite, self).addTest(test)

    def customize(self, args):
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

    def _removeTestAtIndex(self, index):
        """
        Python 3.x-like version of this function for Python 2.7's sake.
        """
        test = self._tests[index]
        if hasattr(test, "countTestCases"):
            self._removed_tests += test.countTestCases()
        self._tests[index] = None

    def countTestCases(self):
        """
        Python 3.x-like version of this function for Python 2.7's sake.
        """
        cases = self._removed_tests
        for test in self:
            if test:
                cases += test.countTestCases()
        return cases

    def _handleClassSetUpPre38(self, test, result):  # pragma: nocover
        previousClass = getattr(result, "_previousTestClass", None)
        currentClass = test.__class__
        if currentClass == previousClass:
            return
        if result._moduleSetUpFailed:
            return
        if getattr(currentClass, "__unittest_skip__", False):  # pragma: no cover
            return

        try:
            currentClass._classSetupFailed = False
        except TypeError:  # pragma: no cover
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
                currentClass.__unittest_skip__ = True
                currentClass.__unittest_skip_why__ = str(e)
            # -- END of fix
            except Exception as e:  # pragma: no cover
                if isinstance(result, _DebugResult):
                    raise
                currentClass._classSetupFailed = True
                className = util.strclass(currentClass)
                errorName = "setUpClass (%s)" % className
                self._addClassOrModuleLevelException(result, e, errorName)
            finally:
                _call_if_exists(result, "_restoreStdout")

    def _handleClassSetUpPost38(
        self, test, result
    ):  # pragma: no cover -- because it's just like *Pre38
        previousClass = getattr(result, "_previousTestClass", None)
        currentClass = test.__class__
        if currentClass == previousClass:
            return
        if result._moduleSetUpFailed:
            return
        if getattr(currentClass, "__unittest_skip__", False):
            return

        try:
            currentClass._classSetupFailed = False
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
                currentClass.__unittest_skip__ = True
                currentClass.__unittest_skip_why__ = str(e)
            # -- END of fix
            except Exception as e:
                if isinstance(result, _DebugResult):
                    raise
                currentClass._classSetupFailed = True
                className = util.strclass(currentClass)
                self._createClassOrModuleLevelException(
                    result, e, "setUpClass", className
                )
            finally:
                _call_if_exists(result, "_restoreStdout")
                if currentClass._classSetupFailed is True:
                    currentClass.doClassCleanups()
                    if len(currentClass.tearDown_exceptions) > 0:
                        for exc in currentClass.tearDown_exceptions:
                            self._createClassOrModuleLevelException(
                                result, exc[1], "setUpClass", className, info=exc
                            )

    if sys.version_info < (3, 8):  # pragma: no cover
        _handleClassSetUp = _handleClassSetUpPre38
    else:
        _handleClassSetUp = _handleClassSetUpPost38

    def run(self, result):
        """
        Emulate unittest's behavior, with Green-specific changes.
        """
        topLevel = False
        if getattr(result, "_testRunEntered", False) is False:
            result._testRunEntered = topLevel = True

        for index, test in enumerate(self):
            if result.shouldStop:
                break

            if _isnotsuite(test):
                self._tearDownPreviousClass(test, result)
                self._handleModuleFixture(test, result)
                self._handleClassSetUp(test, result)
                result._previousTestClass = test.__class__

                if getattr(test.__class__, "_classSetupFailed", False) or getattr(
                    result, "_moduleSetUpFailed", False
                ):
                    continue

                if not self.allow_stdout:
                    captured_stdout = StringIO()
                    captured_stderr = StringIO()
                    saved_stdout = sys.stdout
                    saved_stderr = sys.stderr
                    sys.stdout = GreenStream(captured_stdout)
                    sys.stderr = GreenStream(captured_stderr)

            test(result)

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
            self._tearDownPreviousClass(None, result)
            self._handleModuleTearDown(result)
            result._testRunEntered = False

        # Special handling for class/module tear-down errors. startTest() and
        # finalize() both trigger communication between the subprocess and
        # the runner process. addError()
        if errors_before != len(result.errors):
            difference = len(result.errors) - errors_before
            result.errors, new_errors = (
                result.errors[:-difference],
                result.errors[-difference:],
            )
            for (test, err) in new_errors:
                # test = ProtoTest()
                test.module = result._previousTestClass.__module__
                test.class_name = result._previousTestClass.__name__
                # test.method_name = 'some method name'
                test.is_class_or_module_teardown_error = True
                test.name = "Error in class or module teardown"
                # test.docstr_part = 'docstr part' # error_holder.description
                result.startTest(test)
                result.addError(test, err)
                result.stopTest(test)
                result.finalize()
        return result
