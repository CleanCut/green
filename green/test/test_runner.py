from __future__ import unicode_literals
import copy
import os
import shutil
import sys
import tempfile
import unittest

from green.config import default_args
from green.loader import loadTargets
from green.output import GreenStream
from green.runner import run

try:
    from io import StringIO
except:
    from StringIO import StringIO


GreenTestRunner = None
class FakeCase(unittest.TestCase):
    def runTest(self):
        pass



class TestRun(unittest.TestCase):


    def setUp(self):
        self.args = copy.deepcopy(default_args)
        self.stream = StringIO()


    def tearDown(self):
        del(self.stream)


    def test_stdout(self):
        """
        run() can use sys.stdout as the stream.
        """
        saved_stdout = sys.stdout
        sys.stdout = self.stream
        run(unittest.TestSuite(), sys.stdout, args=self.args)
        sys.stdout = saved_stdout
        self.assertIn('No Tests Found', self.stream.getvalue())


    def test_GreenStream(self):
        """
        run() can use a GreenStream for output.
        """
        gs = GreenStream(self.stream)
        run(unittest.TestSuite(), gs, args=self.args)
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
        run(FakeCase(), self.stream, self.args)
        self.assertIn('Green', self.stream.getvalue())
        self.assertIn('OK', self.stream.getvalue())


    def test_warnings(self):
        """
        setting warnings='always' doesn't crash
        """
        self.args.warnings = 'always'
        run(FakeCase(), self.stream, self.args)
        self.assertIn('OK', self.stream.getvalue())


    def test_noTestsFound(self):
        """
        When we don't find any tests, we say so.
        """
        run(unittest.TestSuite(), self.stream, self.args)
        self.assertIn('No Tests Found', self.stream.getvalue())


    def test_failedSaysSo(self):
        """
        A failing test case causes the whole run to report 'FAILED'
        """
        class FailCase(unittest.TestCase):
            def runTest(self):
                self.assertTrue(False)
        run(FailCase(), self.stream, self.args)
        self.assertIn('FAILED', self.stream.getvalue())



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
        run(tests, self.stream, self.args)
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
        os.chdir(TestSubprocesses.startdir)
        self.args.subprocesses = 0
        run(tests, self.stream, self.args)
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
        os.chdir(TestSubprocesses.startdir)
        self.args.subprocesses = 2
        self.args.run_coverage = True
        run(tests, self.stream, self.args)
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
        os.chdir(TestSubprocesses.startdir)
        self.args.subprocesses = 2
        self.assertRaises(ImportError, run, tests, self.stream, self.args)


    def test_empty(self):
        """
        GreenTestRunner.run() does not crash with empty suite and subprocesses
        """
        suite = unittest.TestSuite()
        self.args.subprocesses = 2
        self.args.termcolor = False
        run(suite, self.stream, self.args)
