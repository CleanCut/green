import unittest

try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock

from green.subprocess import SubprocessLogger, DaemonlessProcess
import green.subprocess


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
        saved_get_logger = green.subprocess.multiprocessing.get_logger
        mock_logger = MagicMock()
        def addHandler(ignore):
            mock_logger.handlers = [MagicMock()]
        mock_logger.addHandler = addHandler
        mock_logger.handlers = False
        mock_get_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        green.subprocess.multiprocessing.get_logger = mock_get_logger
        def func():
            raise AttributeError
        l = SubprocessLogger(func)
        self.assertRaises(AttributeError, l)
        mock_get_logger.assert_called()
        green.subprocess.multiprocessing.get_logger = saved_get_logger



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
