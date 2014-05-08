import os
import shutil
import tempfile
import unittest

from green import loader



class TestGetTests(unittest.TestCase):


    def test_emptyDirAbsolute(self):
        "Absolute path to empty directory returns None"
        tmpdir = tempfile.mkdtemp()
        try:
            tests = loader.getTests(tmpdir)
        except:
            raise
        finally:
            shutil.rmtree(tmpdir)
        self.assertTrue(tests == None)


    def test_emptyDirRelative(self):
        "Relative path to empty directory returns None"
        tmpdir = tempfile.mkdtemp()
        try:
            os.chdir(tmpdir)
            os.chdir('..')
            tests = loader.getTests(os.path.dirname(tmpdir))
        except:
            raise
        finally:
            shutil.rmtree(tmpdir)
        self.assertTrue(tests == None)


    def test_emptyDirDot(self):
        "'.' while in an empty directory returns None"
        tmpdir = tempfile.mkdtemp()
        try:
            os.chdir(tmpdir)
            tests = loader.getTests('.')
        except:
            raise
        finally:
            shutil.rmtree(tmpdir)
        self.assertTrue(tests == None)
