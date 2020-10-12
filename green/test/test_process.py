from ctypes import c_double
import os
import multiprocessing
import shutil
import tempfile
from textwrap import dedent
import unittest

try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock

from green.process import ProcessLogger, DaemonlessProcess, poolRunner
from green import process

try:
    from Queue import Queue, Empty
except:
    from queue import Queue, Empty


class TestProcessLogger(unittest.TestCase):
    def test_callThrough(self):
        """
        Calls are passed through to the wrapped callable
        """
        message = "some message"

        def func():
            return message

        l = ProcessLogger(func)
        self.assertEqual(l(), message)

    def test_exception(self):
        """
        A raised exception gets re-raised
        """
        saved_get_logger = process.multiprocessing.get_logger
        mock_logger = MagicMock()

        def addHandler(ignore):
            mock_logger.handlers = [MagicMock()]

        mock_logger.addHandler = addHandler
        mock_logger.handlers = False
        mock_get_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        process.multiprocessing.get_logger = mock_get_logger
        self.addCleanup(
            setattr, process.multiprocessing, "get_logger", saved_get_logger
        )

        def func():
            raise AttributeError

        l = ProcessLogger(func)
        self.assertRaises(AttributeError, l)
        mock_get_logger.assert_any_call()


class TestDaemonlessProcess(unittest.TestCase):
    def test_daemonIsFalse(self):
        """
        No matter what daemon is set to, it returns False
        """
        dp = DaemonlessProcess()
        self.assertEqual(dp.daemon, False)
        dp.daemon = True
        self.assertEqual(dp.daemon, False)
        dp.daemon = 5
        self.assertEqual(dp.daemon, False)
        dp.daemon = ["something"]
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
        """
        Runs normally
        """
        saved_coverage = process.coverage
        process.coverage = MagicMock()
        self.addCleanup(setattr, process, "coverage", saved_coverage)
        # Parent directory setup
        os.chdir(self.tmpdir)
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        basename = os.path.basename(sub_tmpdir)
        # Child setup
        fh = open(os.path.join(basename, "__init__.py"), "w")
        fh.write("\n")
        fh.close()
        fh = open(os.path.join(basename, "test_pool_runner_dotted.py"), "w")
        fh.write(
            dedent(
                """
            import unittest
            class A(unittest.TestCase):
                def testPass(self):
                    pass
            """
            )
        )
        fh.close()
        module_name = basename + ".test_pool_runner_dotted.A.testPass"
        result = Queue()
        poolRunner(module_name, result, 1)
        result.get()
        self.assertEqual(len(result.get().passing), 1)

    def test_SyntaxErrorInUnitTest(self):
        """
        SyntaxError gets reported as an error loading the unit test
        """
        saved_coverage = process.coverage
        process.coverage = MagicMock()
        self.addCleanup(setattr, process, "coverage", saved_coverage)
        # Parent directory setup
        os.chdir(self.tmpdir)
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        basename = os.path.basename(sub_tmpdir)
        # Child setup
        fh = open(os.path.join(basename, "__init__.py"), "w")
        fh.write("\n")
        fh.close()
        fh = open(os.path.join(basename, "test_pool_syntax_error.py"), "w")
        fh.write("aoeu")
        fh.close()
        result = Queue()
        poolRunner(basename, result, 1)
        result.get()
        self.assertEqual(len(result.get().errors), 1)

    def test_error(self):
        """
        Exception raised running unit test is reported as an error
        """
        # Parent directory setup
        os.chdir(self.tmpdir)
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        basename = os.path.basename(sub_tmpdir)
        # Child setup
        fh = open(os.path.join(basename, "__init__.py"), "w")
        fh.write("\n")
        fh.close()
        fh = open(os.path.join(basename, "test_pool_runner_dotted_fail.py"), "w")
        fh.write(
            dedent(
                """
            import unittest
            class A(unittest.TestCase):
                def testError(self):
                    raise AttributeError
            """
            )
        )
        fh.close()
        module_name = basename + ".test_pool_runner_dotted_fail.A.testError"
        result = Queue()
        poolRunner(module_name, result)
        result.get()
        self.assertEqual(len(result.get().errors), 1)

    def test_bad_attr(self):
        """
        Accessing a bad attribute is only reported once (see #150)
        """
        # Parent directory setup
        os.chdir(self.tmpdir)
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        basename = os.path.basename(sub_tmpdir)
        # Child setup
        fh = open(os.path.join(basename, "__init__.py"), "w")
        fh.write("\n")
        fh.close()
        fh = open(os.path.join(basename, "test_pool_runner_bad_attr.py"), "w")
        fh.write(
            dedent(
                """
            import unittest
            class A(unittest.TestCase):
                def testBadAttr(self):
                    "".garbage
            """
            )
        )
        fh.close()
        module_name = basename + ".test_pool_runner_bad_attr.A.testBadAttr"
        result = Queue()
        poolRunner(module_name, result)
        result.get_nowait()  # should get the target name
        result.get_nowait()  # should get the result
        result.get_nowait()  # should get None
        # should raise Empty unless the extra result bug is present
        self.assertRaises(Empty, result.get_nowait)

    def test_process(self):
        """
                Avoid FileNotFoundError when using a multiprocessing.Value, fixes #154.
                This test never fails, we have to watch the outer stderr to see if we get output like this:

          File "/usr/local/Cellar/python3/3.5.2_3/Frameworks/Python.framework/Versions/3.5/lib/python3.5/multiprocessing/util.py", line 254, in _run_finalizers
            finalizer()
          File "/usr/local/Cellar/python3/3.5.2_3/Frameworks/Python.framework/Versions/3.5/lib/python3.5/multiprocessing/util.py", line 186, in __call__
            res = self._callback(*self._args, **self._kwargs)
          File "/usr/local/Cellar/python3/3.5.2_3/Frameworks/Python.framework/Versions/3.5/lib/python3.5/shutil.py", line 465, in rmtree
            onerror(os.lstat, path, sys.exc_info())
          File "/usr/local/Cellar/python3/3.5.2_3/Frameworks/Python.framework/Versions/3.5/lib/python3.5/shutil.py", line 463, in rmtree
            orig_st = os.lstat(path)
        FileNotFoundError: [Errno 2] No such file or directory: '/var/folders/8y/cgqfhxyn2fz3r8n627_6dm_m0000gn/T/tmpp3fobx6i/pymp-8hpbali9'

                Newer versions of Python want to do their own cleanup, so let them.
        """
        val = multiprocessing.Value(c_double, 0)
        # The error happens when something tries to clean up a sub-temporary
        # directory that they assume will always be there to be cleaned up.
