import os
import shutil
import tempfile
import unittest

try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock

from green.subprocess import SubprocessLogger, DaemonlessProcess, poolRunner
from green import subprocess


class TestSubprocessLogger(unittest.TestCase):


    def test_callThrough(self):
        "Calls are passed through to the wrapped callable"
        message = "some message"
        def func():
            return message
        l = SubprocessLogger(func)
        self.assertEqual(l(), message)


    def test_exception(self):
        "A raised exception gets re-raised"
        saved_get_logger = subprocess.multiprocessing.get_logger
        mock_logger = MagicMock()
        def addHandler(ignore):
            mock_logger.handlers = [MagicMock()]
        mock_logger.addHandler = addHandler
        mock_logger.handlers = False
        mock_get_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        subprocess.multiprocessing.get_logger = mock_get_logger
        def func():
            raise AttributeError
        l = SubprocessLogger(func)
        self.assertRaises(AttributeError, l)
        mock_get_logger.assert_called()
        subprocess.multiprocessing.get_logger = saved_get_logger



class TestDaemonlessProcess(unittest.TestCase):


    def test_daemonIsFalse(self):
        "No matter what daemon is set to, it returns False"
        dp = DaemonlessProcess()
        self.assertEqual(dp.daemon, False)
        dp.daemon = True
        self.assertEqual(dp.daemon, False)
        dp.daemon = 5
        self.assertEqual(dp.daemon, False)
        dp.daemon = ['something']
        self.assertEqual(dp.daemon, False)
        dp.daemon = []
        self.assertEqual(dp.daemon, False)



class TestPoolRunner(unittest.TestCase):


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
    def test_normalRun(self):
        "Runs normally"
        saved_coverage = subprocess.coverage
        subprocess.coverage = MagicMock()
        # Parent directory setup
        os.chdir(self.tmpdir)
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        basename = os.path.basename(sub_tmpdir)
        # Child setup
        fh = open(os.path.join(basename, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        fh = open(os.path.join(basename, 'test_pool_runner_dotted.py'), 'w')
        fh.write("""\
import unittest
class A(unittest.TestCase):
    def testPass(self):
        pass
""")
        fh.close()
        module_name = basename + '.test_pool_runner_dotted.A.testPass'
        result = poolRunner(module_name, 1)
        subprocess.coverage = saved_coverage
        self.assertEqual(len(result.passing), 1)


    def test_SyntaxErrorInUnitTest(self):
        "SyntaxError gets reported as an error loading the unit test"
        saved_coverage = subprocess.coverage
        subprocess.coverage = MagicMock()
        # Parent directory setup
        os.chdir(self.tmpdir)
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        basename = os.path.basename(sub_tmpdir)
        # Child setup
        fh = open(os.path.join(basename, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        fh = open(os.path.join(basename, 'test_pool_syntax_error.py'), 'w')
        fh.write("aoeu")
        fh.close()
        module_name = basename + '.test_pool_syntax_error'
        result = poolRunner(module_name, 1)
        subprocess.coverage = saved_coverage
        self.assertEqual(len(result.errors), 1)


    def test_error(self):
        "Exception raised running unit test is reported as an error"
        # Parent directory setup
        os.chdir(self.tmpdir)
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        basename = os.path.basename(sub_tmpdir)
        # Child setup
        fh = open(os.path.join(basename, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        fh = open(os.path.join(basename, 'test_pool_runner_dotted_fail.py'), 'w')
        fh.write("""\
import unittest
class A(unittest.TestCase):
    def testError(self):
        raise AttributeError
""")
        fh.close()
        module_name = basename + '.test_pool_runner_dotted_fail.A.testError'
        result = poolRunner(module_name)
        self.assertEqual(len(result.errors), 1)


