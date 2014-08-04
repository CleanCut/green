from __future__ import unicode_literals
import os
import shutil
import tempfile
import time
import unittest

from green.loader import loadTargets
from green.runner import GreenTestRunner
from green.output import GreenStream

try:
    from io import StringIO
except:
    from StringIO import StringIO



class TestGreenTestRunner(unittest.TestCase):


    def setUp(self):
        self.stream = StringIO()


    def tearDown(self):
        del(self.stream)


    def test_instantiate(self):
        """
        GreenTestRunner can be instantiated and creates a default stream.
        """
        gtr = GreenTestRunner(self.stream)
        self.assertTrue(type(gtr.stream), GreenStream)


    def test_HTML(self):
        """
        html=True causes html output
        """
        class FakeCase(unittest.TestCase):
            def runTest(self):
                pass
        gtr = GreenTestRunner(self.stream, html=True, subprocesses=1)
        gtr.run(FakeCase())
        self.assertIn('<', self.stream.getvalue())


    def test_verbose3(self):
        """
        verbose=3 causes version output, and an empty test case passes.
        """
        class FakeCase(unittest.TestCase):
            def runTest(self):
                pass
        gtr = GreenTestRunner(self.stream, verbosity=3, subprocesses=1)
        gtr.run(FakeCase())
        self.assertTrue('Green' in self.stream.getvalue())
        self.assertTrue('OK' in self.stream.getvalue())


    def test_warnings(self):
        """
        setting warnings='always' doesn't crash
        """
        class FakeCase(unittest.TestCase):
            def runTest(self):
                pass
        gtr = GreenTestRunner(self.stream, warnings='always', subprocesses=1)
        gtr.run(FakeCase())


    def test_noTestsFound(self):
        """
        When we don't find any tests, we say so.
        """
        gtr = GreenTestRunner(self.stream, subprocesses=1)
        gtr.run(unittest.TestSuite())
        self.assertTrue('No Tests Found' in self.stream.getvalue())


    def test_failedSaysSo(self):
        """
        A failing test case causes the whole run to report 'FAILED'
        """
        class FailCase(unittest.TestCase):
            def runTest(self):
                self.assertTrue(False)
        gtr = GreenTestRunner(self.stream, subprocesses=1)
        gtr.run(FailCase())
        self.assertTrue('FAILED' in self.stream.getvalue())



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
        gtr = GreenTestRunner(self.stream, subprocesses=2, termcolor=False)
        gtr.run(tests)
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
        gtr = GreenTestRunner(self.stream, subprocesses=2, run_coverage=True)
        gtr.run(tests)


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
        gtr = GreenTestRunner(self.stream, subprocesses=2, termcolor=False)
        self.assertRaises(ImportError, gtr.run, (tests,))


    def test_empty(self):
        """
        GreenTestRunner.run() does not crash with empty suite and subprocesses
        """
        suite = unittest.TestSuite()
        gtr = GreenTestRunner(self.stream, subprocesses=2, termcolor=False)
        gtr.run(suite)
