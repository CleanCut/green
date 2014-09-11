from __future__ import unicode_literals
from __future__ import print_function

import unittest
try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock

from green.suite import GreenTestSuite
from green.config import default_args



class TestGreenTestSuite(unittest.TestCase):

    def test_empty(self):
        """
        An empty suite can be instantiated.
        """
        GreenTestSuite()


    def test_defaultArgs(self):
        """
        Passing in default arguments causes attributes to be set.
        """
        gts = GreenTestSuite(args=default_args)
        self.assertEqual(gts.allow_stdout, default_args.allow_stdout)


    def test_shouldStop(self):
        """
        When result.shouldStop == True, the suite should exit early.
        """
        mock_test = MagicMock()
        gts = GreenTestSuite(args=default_args)
        gts._tests = (mock_test,)
        mock_result = MagicMock()
        mock_result.shouldStop = True
        gts.run(mock_result)

    def test_failedSetup(self):
        """
        When class setup fails, we skip to the next test.
        """
        mock_test = MagicMock()
        mock_test.__iter__.side_effect = TypeError
        gts = GreenTestSuite(args=default_args)
        gts._tests = (mock_test,)
        mock_result = MagicMock()
        mock_result._moduleSetUpFailed = True
        mock_result.shouldStop = False
        gts.run(mock_result)
