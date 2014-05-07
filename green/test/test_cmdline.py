import os
import shutil
import tempfile
import unittest

from green import cmdline



class TestGetTests(unittest.TestCase):


    def test_emptyDirAbsolute(self):
        "Absolute path to empty directory returns None"
        tmpdir = tempfile.mkdtemp()
        try:
            tests = cmdline.getTests(tmpdir)
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
            tests = cmdline.getTests(os.path.dirname(tmpdir))
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
            tests = cmdline.getTests('.')
        except:
            raise
        finally:
            shutil.rmtree(tmpdir)
        self.assertTrue(tests == None)
