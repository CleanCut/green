import copy
from io import StringIO
import os
import pathlib
import platform
import shutil
import signal
import sys
import tempfile
from textwrap import dedent
import unittest
from unittest import mock
import weakref

from green.config import default_args
from green.exceptions import InitializerOrFinalizerError
from green.loader import GreenTestLoader
from green.output import GreenStream
from green.runner import InitializerOrFinalizer, run
from green.suite import GreenTestSuite


skip_testtools = False
try:
    import testtools

    testtools
except:
    skip_testtools = True


# --- Helper stuff ---

importable_function_worked = False


def _importableFunction():
    """
    Used by TestInitializerOrFinalizer.test_importable()
    """
    global importable_function_worked
    importable_function_worked = True


non_callable = None  # Used by TestInitializerOrFinalizer.test_not_callable()


def _crashy():
    """
    Used by TestInitializerOrFinalizer.test_crash()
    """
    raise AssertionError("Oops!  I crashed.")


# --- End of helper stuff


class TestInitializerOrFinalizer(unittest.TestCase):
    def test_blank(self):
        """
        Given a blank dotted function, calling the initializer/finalizer does
        nothing.
        """
        initializer = InitializerOrFinalizer("")
        initializer()

    def test_unimportable(self):
        """
        Given an unimportable module, an InitializerOrFinalizerError is raised.
        """
        initializer = InitializerOrFinalizer("garbagejunk.nonexistant")
        self.assertRaises(InitializerOrFinalizerError, initializer)

    def test_importable(self):
        """
        Given an actual importable module and function, the function is run.
        """
        global importable_function_worked
        importable_function_worked = False
        InitializerOrFinalizer("green.test.test_runner._importableFunction")()
        self.assertTrue(importable_function_worked)

    def test_not_callable(self):
        """
        An importable, but not-callable-object also raises an
        InitializerOrFinalizerError.
        """
        initializer = InitializerOrFinalizer("green.test.test_runner.non_callable")
        self.assertRaises(InitializerOrFinalizerError, initializer)

    def test_crash(self):
        """
        An importable, callable object...crashes.
        """
        initializer = InitializerOrFinalizer("green.test.test_runner._crashy")
        self.assertRaises(InitializerOrFinalizerError, initializer)


class TestRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.startdir = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        if os.getcwd() != cls.startdir:
            os.chdir(cls.startdir)
        cls.startdir = None

    def setUp(self):
        self.args = copy.deepcopy(default_args)
        self.stream = StringIO()
        self.tmpdir = tempfile.mkdtemp()
        self.loader = GreenTestLoader()

    def tearDown(self):
        del self.tmpdir
        del self.stream

    def test_stdout(self):
        """
        run() can use sys.stdout as the stream.
        """
        saved_stdout = sys.stdout
        sys.stdout = self.stream
        self.addCleanup(setattr, sys, "stdout", saved_stdout)
        run(GreenTestSuite(), sys.stdout, args=self.args)
        self.assertIn("No Tests Found", self.stream.getvalue())

    def test_green_stream(self):
        """
        run() can use a GreenStream for output.
        """
        gs = GreenStream(self.stream)
        run(GreenTestSuite(), gs, args=self.args)
        self.assertIn("No Tests Found", self.stream.getvalue())

    def test_verbose3(self):
        """
        verbose=3 causes version output, and an empty test case passes.
        """
        self.args.verbose = 3
        sub_tmpdir = pathlib.Path(tempfile.mkdtemp(dir=self.tmpdir))
        content = dedent(
            """
            import unittest
            class Verbose3(unittest.TestCase):
                def test01(self):
                    pass
            """
        )
        (sub_tmpdir / "test_verbose3.py").write_text(content, encoding="utf-8")
        os.chdir(sub_tmpdir)
        try:
            tests = self.loader.loadTargets("test_verbose3")
            result = run(tests, self.stream, self.args)
        finally:
            os.chdir(self.startdir)
        self.assertEqual(result.testsRun, 1)
        self.assertIn("Green", self.stream.getvalue())
        self.assertIn("OK", self.stream.getvalue())

    def test_warnings(self):
        """
        setting warnings='always' doesn't crash
        """
        self.args.warnings = "always"
        sub_tmpdir = pathlib.Path(tempfile.mkdtemp(dir=self.tmpdir))
        content = dedent(
            """
            import unittest
            class Warnings(unittest.TestCase):
                def test01(self):
                    pass
            """
        )
        (sub_tmpdir / "test_warnings.py").write_text(content, encoding="utf-8")
        os.chdir(sub_tmpdir)
        try:
            tests = self.loader.loadTargets("test_warnings")
            result = run(tests, self.stream, self.args)
        finally:
            os.chdir(self.startdir)
        self.assertEqual(result.testsRun, 1)
        self.assertIn("OK", self.stream.getvalue())

    def test_no_tests_found(self):
        """
        When we don't find any tests, we say so.
        """
        result = run(GreenTestSuite(), self.stream, self.args)
        self.assertIn("No Tests Found", self.stream.getvalue())
        self.assertEqual(result.testsRun, 0)
        self.assertEqual(result.wasSuccessful(), False)

    def test_failed_says_so(self):
        """
        A failing test case causes the whole run to report 'FAILED'
        """
        sub_tmpdir = pathlib.Path(tempfile.mkdtemp(dir=self.tmpdir))
        content = dedent(
            """
            import unittest
            class Failed(unittest.TestCase):
                def test01(self):
                    self.assertTrue(False)
            """
        )
        (sub_tmpdir / "test_failed.py").write_text(content, encoding="utf-8")
        os.chdir(sub_tmpdir)
        try:
            tests = self.loader.loadTargets("test_failed")
            result = run(tests, self.stream, self.args)
        finally:
            os.chdir(self.startdir)
        self.assertEqual(result.testsRun, 1)
        self.assertIn("FAILED", self.stream.getvalue())

    def test_failfast(self):
        """
        failfast causes the testing to stop after the first failure.
        """
        sub_tmpdir = pathlib.Path(tempfile.mkdtemp(dir=self.tmpdir))
        content = dedent(
            """
            import unittest
            class SIGINTCase(unittest.TestCase):
                def test00(self):
                    raise Exception
                def test01(self):
                    pass
            """
        )
        (sub_tmpdir / "test_failfast.py").write_text(content, encoding="utf-8")
        os.chdir(sub_tmpdir)
        try:
            tests = self.loader.loadTargets("test_failfast")
            self.args.failfast = True
            result = run(tests, self.stream, self.args)
        finally:
            os.chdir(self.startdir)
        self.assertEqual(result.testsRun, 1)

    def test_system_exit(self):
        """
        Raising a SystemExit gets caught and reported.
        """
        sub_tmpdir = pathlib.Path(tempfile.mkdtemp(dir=self.tmpdir))
        content = dedent(
            """
            import unittest
            class SystemExitCase(unittest.TestCase):
                def test00(self):
                    raise SystemExit(1)
                def test01(self):
                    pass
            """
        )
        (sub_tmpdir / "test_systemexit.py").write_text(content, encoding="utf-8")
        os.chdir(sub_tmpdir)
        try:
            tests = self.loader.loadTargets("test_systemexit")
            result = run(tests, self.stream, self.args)
        finally:
            os.chdir(self.startdir)
        self.assertEqual(result.testsRun, 2)


class TestProcesses(unittest.TestCase):
    # Setup
    @classmethod
    def setUpClass(cls):
        cls.startdir = os.getcwd()
        cls.container_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        if os.getcwd() != cls.startdir:
            os.chdir(cls.startdir)
        cls.startdir = None
        shutil.rmtree(cls.container_dir)

    def setUp(self):
        os.chdir(self.container_dir)
        self.tmpdir = tempfile.mkdtemp(dir=self.container_dir)
        self.stream = StringIO()
        self.args = copy.deepcopy(default_args)
        self.loader = GreenTestLoader()

    def tearDown(self):
        os.chdir(self.startdir)
        # On windows, the processes block access to the files while
        # they take a bit to clean themselves up.
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        del self.stream

    @unittest.skipIf(platform.system() == "Windows", "Windows doesn't have SIGINT.")
    def test_catch_process_sigint(self):
        """
        run() can catch SIGINT while running a process.
        """
        # Mock the list of TestResult instances that should be stopped,
        # otherwise the actual TestResult that is running this test will be
        # told to stop when we send SIGINT
        sub_tmpdir = pathlib.Path(tempfile.mkdtemp(dir=self.tmpdir))
        saved__results = unittest.signals._results
        unittest.signals._results = weakref.WeakKeyDictionary()
        self.addCleanup(setattr, unittest.signals, "_results", saved__results)
        content = dedent(
            """
            import os
            import signal
            import unittest
            class TestSigint(unittest.TestCase):
                def test_00(self):
                    os.kill({}, signal.SIGINT)
            """
        ).format(os.getpid())
        (sub_tmpdir / "test_sigint.py").write_text(content, encoding="utf-8")
        os.chdir(sub_tmpdir)
        try:
            tests = self.loader.loadTargets("test_sigint")
            self.args.processes = 2
            run(tests, self.stream, self.args)
        finally:
            os.chdir(TestProcesses.startdir)

    def test_collision_protection(self):
        """
        If tempfile.gettempdir() is used for dir, using same testfile name will
        not collide.
        """
        sub_tmpdir = pathlib.Path(tempfile.mkdtemp(dir=self.tmpdir))
        # Child setup
        # pkg/__init__.py
        (sub_tmpdir / "__init__.py").write_text("\n", encoding="utf-8")
        # pkg/some_module.py
        (sub_tmpdir / "some_module.py").write_text("a = 1\n", encoding="utf-8")
        # pkg/test/__init__.py
        os.mkdir(sub_tmpdir / "test")
        (sub_tmpdir / "test/__init__.py").write_text("\n", encoding="utf-8")
        # pkg/test/test_some_module.py
        content = dedent(
            """
            import os
            import tempfile
            import time
            import unittest
            import {}.some_module
            class A(unittest.TestCase):
                def setUp(self):
                    self.tmpdir = tempfile.gettempdir()
                    self.filename = os.path.join(tempfile.gettempdir(), 'file.txt')
                def testOne(self):
                    for msg in [str(x) for x in range(50)]:
                        fh = open(self.filename, 'w')
                        fh.write(msg)
                        fh.close()
                        time.sleep(.01)
                        fh = open(self.filename)
                        actual = fh.read()
                        fh.close()
                        self.assertEqual(msg, actual)
                def testTwo(self):
                    for msg in [str(x) for x in range(50,100)]:
                        fh = open(self.filename, 'w')
                        fh.write(msg)
                        fh.close()
                        time.sleep(.01)
                        fh = open(self.filename)
                        actual = fh.read()
                        fh.close()
                        self.assertEqual(msg, actual)
            """
        ).format(os.path.basename(sub_tmpdir))
        (sub_tmpdir / "test/test_some_module.py").write_text(content, encoding="utf-8")
        # Load the tests
        os.chdir(self.tmpdir)
        try:
            tests = self.loader.loadTargets(".")
            self.args.processes = 2
            self.args.termcolor = False
            try:
                run(tests, self.stream, self.args)
            except KeyboardInterrupt:
                os.kill(os.getpid(), signal.SIGINT)
        finally:
            os.chdir(TestProcesses.startdir)
        self.assertIn("OK", self.stream.getvalue())

    def test_detect_num_processes(self):
        """
        args.processes = 0 causes auto-detection of number of processes.
        """
        sub_tmpdir = pathlib.Path(tempfile.mkdtemp(dir=self.tmpdir))
        (sub_tmpdir / "__init__.py").write_text("\n", encoding="utf-8")
        content = dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPasses(self):
                    pass"""
        )
        (sub_tmpdir / "test_detectNumProcesses.py").write_text(
            content, encoding="utf-8"
        )
        # Load the tests
        os.chdir(self.tmpdir)
        try:
            tests = self.loader.loadTargets(".")
            self.args.processes = 0
            run(tests, self.stream, self.args)
        finally:
            os.chdir(TestProcesses.startdir)
        self.assertIn("OK", self.stream.getvalue())

    def test_run_coverage(self):
        """
        Running coverage in process mode doesn't crash.
        """
        try:
            import coverage
        except ImportError:
            self.skipTest("Coverage needs to be installed for this test")
        self.assertTrue(coverage.version_info)
        sub_tmpdir = pathlib.Path(tempfile.mkdtemp(dir=self.tmpdir))
        (sub_tmpdir / "__init__.py").write_text("\n", encoding="utf-8")
        content = dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPasses(self):
                    pass"""
        )
        (sub_tmpdir / "test_coverage.py").write_text(content, encoding="utf-8")
        # Load the tests
        os.chdir(self.tmpdir)
        try:
            tests = self.loader.loadTargets(".")
            self.args.processes = 2
            self.args.run_coverage = True
            self.args.cov = mock.MagicMock()
            run(tests, self.stream, self.args, testing=True)
        finally:
            os.chdir(TestProcesses.startdir)
        self.assertIn("OK", self.stream.getvalue())

    def test_bad_test(self):
        """
        Bad syntax in a testfile is caught as a test error.
        """
        sub_tmpdir = pathlib.Path(tempfile.mkdtemp(dir=self.tmpdir))
        (sub_tmpdir / "__init__.py").write_text("\n", encoding="utf-8")
        (sub_tmpdir / "test_bad_syntax.py").write_text("aoeu", encoding="utf-8")
        # Load the tests
        os.chdir(self.tmpdir)
        try:
            tests = self.loader.loadTargets(".")
            self.args.processes = 2
        finally:
            os.chdir(TestProcesses.startdir)
        self.assertRaises(ImportError, run, tests, self.stream, self.args)

    def test_uncaught_exception(self):
        """
        Exceptions that escape the test framework get caught by poolRunner and
        reported as a failure.  For example, the testtools implementation of
        TestCase unwisely (but deliberately) lets SystemExit exceptions
        through.
        """
        if skip_testtools:
            self.skipTest("testtools must be installed to run this test.")

        sub_tmpdir = pathlib.Path(tempfile.mkdtemp(dir=self.tmpdir))
        # pkg/__init__.py
        (sub_tmpdir / "__init__.py").write_text("\n", encoding="utf-8")
        content = dedent(
            """
            import testtools
            class Uncaught(testtools.TestCase):
                def test_uncaught(self):
                    raise SystemExit(0)
            """
        )
        (sub_tmpdir / "test_uncaught.py").write_text(content, encoding="utf-8")
        # Load the tests
        os.chdir(self.tmpdir)
        try:
            tests = self.loader.loadTargets(".")
            self.args.processes = 2
            run(tests, self.stream, self.args)
        finally:
            os.chdir(TestProcesses.startdir)
        self.assertIn("FAILED", self.stream.getvalue())

    def test_empty(self):
        """
        run() does not crash with empty suite and processes
        """
        suite = GreenTestSuite()
        self.args.processes = 2
        self.args.termcolor = False
        run(suite, self.stream, self.args)
