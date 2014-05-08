import os
import shutil
import sys
import tempfile
import unittest

from green import loader



class TestGetTestsDirs(unittest.TestCase):


    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()


    def tearDown(self):
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
        self.assertTrue(tests == None)


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
        sys.path.insert(0, os.getcwd())
        # Child setup
        target = os.path.join(self.tmpdir, '__init__.py')
        fh = open(target, 'w')
        fh.write('# pragma nocover')
        fh.close()
        # Load the tests
        module_name = os.path.basename(self.tmpdir)
        tests = loader.getTests(module_name)
        self.assertTrue(tests == None)
