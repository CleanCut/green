from __future__ import unicode_literals
import os
import shutil
import sys
import tempfile
import unittest

from green import loader



class TestGetTests(unittest.TestCase):

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


    def tearDown(self):
        os.chdir(self.container_dir)
        shutil.rmtree(self.tmpdir)


    # Tests
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


    def test_BigDirWithAbsoluteImports(self):
        "Big dir discovers tests and doesn't crash on absolute import"
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        # Child setup
        # pkg/__init__.py
        fh = open(os.path.join(sub_tmpdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        # pkg/target_module.py
        fh = open(os.path.join(sub_tmpdir, 'target_module.py'), 'w')
        fh.write('a = 1\n')
        fh.close()
        # pkg/test/__init__.py
        os.mkdir(os.path.join(sub_tmpdir, 'test'))
        fh = open(os.path.join(sub_tmpdir, 'test', '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        # pkg/test/test_target_module.py
        fh = open(os.path.join(sub_tmpdir, 'test', 'test_target_module.py'), 'w')
        fh.write("""\
import unittest
import {}.target_module
class A(unittest.TestCase):
    def testPass(self):
        pass
""".format(sub_tmpdir))
        fh.close()
        # Load the tests
        os.chdir(self.tmpdir)
        tests = loader.getTests('.')
        self.assertEqual(tests.countTestCases(), 1)


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
        os.chdir(self.tmpdir)
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        basename = os.path.basename(sub_tmpdir)
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
        # Child setup

        tmp_subdir = tempfile.mkdtemp(dir=self.tmpdir)
        fh = open(os.path.join(tmp_subdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        fh = open(os.path.join(tmp_subdir, 'test_module.py'), 'w')
        fh.write("""\
import unittest
class A(unittest.TestCase):
    def testPass(self):
        pass
""")
        fh.close()
        # Go somewhere else, but setup the path
        os.chdir(self.startdir)
        sys.path.insert(0, self.tmpdir)
        # Load the tests
        tests = loader.getTests(os.path.basename(tmp_subdir))
        sys.path.remove(self.tmpdir)
        self.assertTrue(tests.countTestCases(), 1)


    def test_ModuleByName(self):
        "A module in a package can be loaded by filename."
        os.chdir(self.tmpdir)
        tmp_subdir = tempfile.mkdtemp(dir=self.tmpdir)
        fh = open(os.path.join(tmp_subdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        named_module = os.path.join(os.path.basename(tmp_subdir),
                                    'named_module.py')
        fh = open(named_module, 'w')
        fh.write("""\
import unittest
class A(unittest.TestCase):
    def testPass(self):
        pass
""")
        fh.close()
        # Load the tests
        tests = loader.getTests(named_module)
        try:
            self.assertEqual(tests.countTestCases(), 1)
        except:
            raise
        finally:
            shutil.rmtree(tmp_subdir)


    def test_MalformedModuleByName(self):
        "We don't crash attempting to load a module with a SyntaxError"
        fh = open(os.path.join(self.tmpdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        malformed_module = os.path.join(os.path.basename(self.tmpdir),
                                    'malformed_module.py')
        fh = open(malformed_module, 'w')
        fh.write("This is a malformed module.")
        fh.close()
        # Load the tests
        tests = loader.getTests(malformed_module)
        self.assertEqual(tests, None)


    def test_partiallyGoodName(self):
        "Don't crash loading module.object with existing module but not object"
        # Parent directory setup
        os.chdir(self.tmpdir)
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        basename = os.path.basename(sub_tmpdir)
        # Child setup
        fh = open(os.path.join(basename, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        fh = open(os.path.join(basename, 'existing_module.py'), 'w')
        fh.write("""\
import unittest
class A(unittest.TestCase):
    def testPass(self):
        pass
""")
        fh.close()
        # Load the tests
        module_name = basename + ".existing_module.nonexistant_object"
        tests = loader.getTests(module_name)
        self.assertEqual(tests, None)

