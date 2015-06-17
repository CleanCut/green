from __future__ import unicode_literals
import copy
import os
import platform
import shutil
import signal
import sys
import tempfile
import unittest
import weakref

from green.config import default_args
from green.loader import loadTargets
from green.output import GreenStream
from green.runner import run
from green.suite import GreenTestSuite

try:
    from io import StringIO
except:
    from StringIO import StringIO


class FakeCase(unittest.TestCase):
    def runTest(self):
        pass


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

    def tearDown(self):
        del(self.tmpdir)
        del(self.stream)

    def test_catchSIGINT(self):
        """
        run() can catch SIGINT with just one process.
        """
        if platform.system() == 'Windows':
            self.skipTest('This test is for posix-specific behavior.')
        # Mock the list of TestResult instances that should be stopped,
        # otherwise the actual TestResult that is running this test will be
        # told to stop when we send SIGINT
        saved__results = unittest.signals._results
        unittest.signals._results = weakref.WeakKeyDictionary()
        class KBICase(unittest.TestCase):
            def runTest(self):
                os.kill(os.getpid(), signal.SIGINT)
        kc = KBICase()
        run(kc, self.stream, self.args)
        unittest.signals._results = saved__results

    def test_stdout(self):
        """
        run() can use sys.stdout as the stream.
        """
        saved_stdout = sys.stdout
        sys.stdout = self.stream
        run(GreenTestSuite(), sys.stdout, args=self.args)
        sys.stdout = saved_stdout
        self.assertIn('No Tests Found', self.stream.getvalue())

    def test_GreenStream(self):
        """
        run() can use a GreenStream for output.
        """
        gs = GreenStream(self.stream)
        run(GreenTestSuite(), gs, args=self.args)
        self.assertIn('No Tests Found', self.stream.getvalue())

    def test_HTML(self):
        """
        html=True causes html output
        """
        self.args.html = True
        run(FakeCase(), self.stream, self.args)
        self.assertIn('<', self.stream.getvalue())

    def test_verbose3(self):
        """
        verbose=3 causes version output, and an empty test case passes.
        """
        self.args.verbose = 3
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        fh = open(os.path.join(sub_tmpdir, 'test_verbose3.py'), 'w')
        fh.write("""
import unittest
class Verbose3(unittest.TestCase):
    def test01(self):
        pass
""".format(os.getpid()))
        fh.close()
        os.chdir(sub_tmpdir)
        tests = loadTargets('test_verbose3')
        result = run(tests, self.stream, self.args)
        os.chdir(self.startdir)
        self.assertEqual(result.testsRun, 1)
        self.assertIn('Green', self.stream.getvalue())
        self.assertIn('OK', self.stream.getvalue())

    def test_warnings(self):
        """
        setting warnings='always' doesn't crash
        """
        self.args.warnings = 'always'
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        fh = open(os.path.join(sub_tmpdir, 'test_warnings.py'), 'w')
        fh.write("""
import unittest
class Warnings(unittest.TestCase):
    def test01(self):
        pass
""".format(os.getpid()))
        fh.close()
        os.chdir(sub_tmpdir)
        tests = loadTargets('test_warnings')
        result = run(tests, self.stream, self.args)
        os.chdir(self.startdir)
        self.assertEqual(result.testsRun, 1)
        self.assertIn('OK', self.stream.getvalue())

    def test_noTestsFound(self):
        """
        When we don't find any tests, we say so.
        """
        run(GreenTestSuite(), self.stream, self.args)
        self.assertIn('No Tests Found', self.stream.getvalue())

    def test_failedSaysSo(self):
        """
        A failing test case causes the whole run to report 'FAILED'
        """
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        fh = open(os.path.join(sub_tmpdir, 'test_failed.py'), 'w')
        fh.write("""
import unittest
class Failed(unittest.TestCase):
    def test01(self):
        self.assertTrue(False)
""".format(os.getpid()))
        fh.close()
        os.chdir(sub_tmpdir)
        tests = loadTargets('test_failed')
        result = run(tests, self.stream, self.args)
        os.chdir(self.startdir)
        self.assertEqual(result.testsRun, 1)
        self.assertIn('FAILED', self.stream.getvalue())

    def test_failfast(self):
        """
        failfast causes the testing to stop after the first failure.
        """
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        fh = open(os.path.join(sub_tmpdir, 'test_failfast.py'), 'w')
        fh.write("""
import unittest
class SIGINTCase(unittest.TestCase):
    def test00(self):
        raise Exception
    def test01(self):
        pass
""".format(os.getpid()))
        fh.close()
        os.chdir(sub_tmpdir)
        tests = loadTargets('test_failfast')
        self.args.failfast = True
        result = run(tests, self.stream, self.args)
        os.chdir(self.startdir)
        self.assertEqual(result.testsRun, 1)


    def test_systemExit(self):
        """
        Raising a SystemExit gets caught and reported.
        """
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        fh = open(os.path.join(sub_tmpdir, 'test_systemexit.py'), 'w')
        fh.write("""
import unittest
class SystemExitCase(unittest.TestCase):
    def test00(self):
        raise SystemExit(1)
    def test01(self):
        pass
""".format(os.getpid()))
        fh.close()
        os.chdir(sub_tmpdir)
        tests = loadTargets('test_systemexit')
        result = run(tests, self.stream, self.args)
        os.chdir(self.startdir)
        self.assertEqual(result.testsRun, 2)



class TestSubprocesses(unittest.TestCase):

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

    def tearDown(self):
        os.chdir(self.startdir)
        # On windows, the subprocesses block access to the files while
        # they take a bit to clean themselves up.
        shutil.rmtree(self.tmpdir)
        del(self.stream)

    def test_catchSubprocessSIGINT(self):
        """
        run() can catch SIGINT while running a subprocess.
        """
        if platform.system() == 'Windows':
            self.skipTest('This test is for posix-specific behavior.')
        # Mock the list of TestResult instances that should be stopped,
        # otherwise the actual TestResult that is running this test will be
        # told to stop when we send SIGINT
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        saved__results = unittest.signals._results
        unittest.signals._results = weakref.WeakKeyDictionary()
        fh = open(os.path.join(sub_tmpdir, 'test_sigint.py'), 'w')
        fh.write("""
import os
import signal
import unittest
class SIGINTCase(unittest.TestCase):
    def test00(self):
        os.kill({}, signal.SIGINT)
""".format(os.getpid()))
        fh.close()
        os.chdir(sub_tmpdir)
        tests = loadTargets('test_sigint')
        self.args.subprocesses = 2
        run(tests, self.stream, self.args)
        unittest.signals._results = saved__results
        os.chdir(TestSubprocesses.startdir)

    def test_collisionProtection(self):
        """
        If tempfile.gettempdir() is used for dir, using same testfile name will
        not collide.
        """
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        # Child setup
        # pkg/__init__.py
        fh = open(os.path.join(sub_tmpdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        # pkg/target_module.py
        fh = open(os.path.join(sub_tmpdir, 'some_module.py'), 'w')
        fh.write('a = 1\n')
        fh.close()
        # pkg/test/__init__.py
        os.mkdir(os.path.join(sub_tmpdir, 'test'))
        fh = open(os.path.join(sub_tmpdir, 'test', '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        # pkg/test/test_target_module.py
        fh = open(os.path.join(sub_tmpdir, 'test', 'test_some_module.py'), 'w')
        fh.write("""\
import os
import tempfile
import unittest
import {}.some_module
class A(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.gettempdir()
        self.filename = os.path.join(tempfile.gettempdir(), 'file.txt')
    def testOne(self):
        for msg in [str(x) for x in range(100)]:
            fh = open(self.filename, 'w')
            fh.write(msg)
            fh.close()
            self.assertEqual(msg, open(self.filename).read())
    def testTwo(self):
        for msg in [str(x) for x in range(100,200)]:
            fh = open(self.filename, 'w')
            fh.write(msg)
            fh.close()
            self.assertEqual(msg, open(self.filename).read())
""".format(os.path.basename(sub_tmpdir)))
        fh.close()
        # Load the tests
        os.chdir(self.tmpdir)
        tests = loadTargets('.')
        self.args.subprocesses = 2
        self.args.termcolor = False
        try:
            run(tests, self.stream, self.args)
        except KeyboardInterrupt:
            os.kill(os.getpid(), signal.SIGINT)
        os.chdir(TestSubprocesses.startdir)
        self.assertIn('OK', self.stream.getvalue())

    def test_detectNumSubprocesses(self):
        """
        args.subprocesses = 0 causes auto-detection of number of subprocesses.
        """
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        # pkg/__init__.py
        fh = open(os.path.join(sub_tmpdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        # pkg/test/test_target_module.py
        fh = open(os.path.join(sub_tmpdir, 'test_autosubprocesses.py'), 'w')
        fh.write("""
import unittest
class A(unittest.TestCase):
    def testPasses(self):
        pass""")
        fh.close()
        # Load the tests
        os.chdir(self.tmpdir)
        tests = loadTargets('.')
        self.args.subprocesses = 0
        run(tests, self.stream, self.args)
        os.chdir(TestSubprocesses.startdir)
        self.assertIn('OK', self.stream.getvalue())

    def test_runCoverage(self):
        """
        Running coverage in subprocess mode doesn't crash
        """
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        # pkg/__init__.py
        fh = open(os.path.join(sub_tmpdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        # pkg/test/test_target_module.py
        fh = open(os.path.join(sub_tmpdir, 'test_coverage.py'), 'w')
        fh.write("""
import unittest
class A(unittest.TestCase):
    def testPasses(self):
        pass""")
        fh.close()
        # Load the tests
        os.chdir(self.tmpdir)
        tests = loadTargets('.')
        self.args.subprocesses = 2
        self.args.run_coverage = True
        run(tests, self.stream, self.args)
        os.chdir(TestSubprocesses.startdir)
        self.assertIn('OK', self.stream.getvalue())

    def test_badTest(self):
        """
        Bad syntax in a testfile is caught as a test error.
        """
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        # pkg/__init__.py
        fh = open(os.path.join(sub_tmpdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        # pkg/test/test_target_module.py
        fh = open(os.path.join(sub_tmpdir, 'test_bad_syntax.py'), 'w')
        fh.write("aoeu")
        fh.close()
        # Load the tests
        os.chdir(self.tmpdir)
        tests = loadTargets('.')
        self.args.subprocesses = 2
        self.assertRaises(ImportError, run, tests, self.stream, self.args)
        os.chdir(TestSubprocesses.startdir)

    def test_uncaughtException(self):
        """
        Exceptions that escape the test framework get caught by poolRunner and
        reported as a failure.  For example, the testtools implementation of
        TestCase unwisely (but deliberately) lets SystemExit exceptions through.
        """
        try:
            import testtools
        except:
            self.skipTest('testtools must be installed to run this test.')
        testtools # Make the linter happy

        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        # pkg/__init__.py
        fh = open(os.path.join(sub_tmpdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        # pkg/test/test_target_module.py
        fh = open(os.path.join(sub_tmpdir, 'test_uncaught.py'), 'w')
        fh.write("""
import testtools
class Uncaught(testtools.TestCase):
    def test_uncaught(self):
        raise SystemExit(0)
        """)
        fh.close()
        # Load the tests
        os.chdir(self.tmpdir)
        tests = loadTargets('.')
        self.args.subprocesses = 2
        run(tests, self.stream, self.args)
        os.chdir(TestSubprocesses.startdir)
        self.assertIn('FAILED', self.stream.getvalue())



    def test_empty(self):
        """
        run() does not crash with empty suite and subprocesses
        """
        suite = GreenTestSuite()
        self.args.subprocesses = 2
        self.args.termcolor = False
        run(suite, self.stream, self.args)
