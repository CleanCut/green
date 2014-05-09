import os
import shutil
import sys
import tempfile
import unittest

from green import loader



class TestGetTests(unittest.TestCase):


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


    def tearDown(self):
        os.chdir(self.container_dir)
        shutil.rmtree(self.tmpdir)


    def test_emptyDirAbsolute(self):
        "Absolute path to empty directory returns None"
        tests = loader.getTests(self.tmpdir)
        self.assertTrue(tests == None)


    def test_emptyDirRelative(self):
        "Relative path to empty directory returns None"
        os.chdir(self.tmpdir)
        os.chdir('..')
        tests = loader.getTests(os.path.dirname(self.tmpdir))
        self.assertEqual(tests, None)


    def test_emptyDirDot(self):
        "'.' while in an empty directory returns None"
        os.chdir(self.tmpdir)
        tests = loader.getTests('.')
        self.assertTrue(tests == None)


    def test_relativeDotDir(self):
        "Dotted relative path to empty directory returns None"
        os.chdir(self.tmpdir)
        os.chdir('..')
        target = os.path.join('.', os.path.basename(self.tmpdir))
        tests = loader.getTests(target)
        self.assertTrue(tests == None)


    def test_DirWithInit(self):
        "Dir empty other than blank __init__.py returns None"
        # Parent directory setup
        os.chdir(self.tmpdir)
        os.chdir('..')
        # Child setup
        target = os.path.join(self.tmpdir, '__init__.py')
        fh = open(target, 'w')
        fh.write('\n')
        fh.close()
        fh = open(os.path.join(self.tmpdir, 'test_module_with_init.py'), 'w')
        fh.write("""\
import unittest
class A(unittest.TestCase):
    def testPass(self):
        pass
""")
        fh.close()
        # Load the tests
        module_name = os.path.basename(self.tmpdir)
        tests = loader.getTests(module_name)
        self.assertEqual(tests.countTestCases(), 1)


    def test_DottedName(self):
        "Importing a module via dotted name loads the tests."
        # Parent directory setup
        basename = os.path.basename(self.tmpdir)
        os.chdir(self.tmpdir)
        os.chdir('..')
        # Child setup
        fh = open(os.path.join(basename, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        fh = open(os.path.join(basename, 'test_module_dotted_name.py'), 'w')
        fh.write("""\
import unittest
class A(unittest.TestCase):
    def testPass(self):
        pass
""")
        fh.close()
        # Load the tests
        module_name = basename + ".test_module_dotted_name"
        tests = loader.getTests(module_name)
        self.assertEqual(tests.countTestCases(), 1)


    def test_DottedNamePackageFromPath(self):
        "Importing a package from path loads the tests."
        # Parent directory setup
        dirname = os.path.dirname(self.tmpdir)
        # Child setup
        fh = open(os.path.join(self.tmpdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        fh = open(os.path.join(self.tmpdir, 'test_module.py'), 'w')
        fh.write("""\
import unittest
class A(unittest.TestCase):
    def testPass(self):
        pass
""")
        fh.close()
        # Load the tests
        tests = loader.getTests(os.path.basename(self.tmpdir))
        self.assertTrue(tests.countTestCases() == 1)


