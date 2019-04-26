from __future__ import unicode_literals
from __future__ import print_function

import copy
from io import StringIO
import os
import tempfile
from textwrap import dedent
import unittest


try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock

from green.config import default_args
from green.loader import GreenTestLoader
from green.runner import run
from green.suite import GreenTestSuite


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

    def test_failedModuleSetup(self):
        """
        When module setup fails, we skip to the next test.
        """
        mock_test = MagicMock()
        mock_test.__iter__.side_effect = TypeError
        gts = GreenTestSuite(args=default_args)
        gts._tests = (mock_test,)
        mock_result = MagicMock()
        mock_result._moduleSetUpFailed = True
        mock_result.shouldStop = False
        gts.run(mock_result)

    def test_addTest_testPattern(self):
        """
        Setting test_pattern will cause a test to be filtered.
        """
        mock_test = MagicMock()
        mock_test._testMethodName = 'test_hello'
        mock_test2 = MagicMock()
        mock_test2._testMethodName = 'test_goodbye'
        args = copy.deepcopy(default_args)
        args.test_pattern = '_good*'
        gts = GreenTestSuite(args=args)
        gts.addTest(mock_test)
        self.assertEqual(gts._tests, [])
        gts.addTest(mock_test2)
        self.assertEqual(gts._tests, [mock_test2])

    def test_allow_stdout(self):
        """
        The allow_stdout setting should not get ignored.
        """
        class Object(object):
            pass
        args = Object()
        args.allow_stdout = True
        gts = GreenTestSuite(args=args)
        self.assertEqual(gts.allow_stdout, True)


    def test_skip_in_setUpClass(self):
        """
        If SkipTest is raised in setUpClass, then the test gets skipped
        """
        gts =  GreenTestSuite(args=default_args)
        mock_test = MagicMock()
        mock_result = MagicMock()
        mock_class = MagicMock()
        mock_result._previousTestClass = None
        mock_result._moduleSetUpFailed = None
        mock_result.__unittest_skip__ = None
        mock_test.__class__ = mock_class
        mock_class.setUpClass.side_effect = unittest.SkipTest("kaboom")

        gts._handleClassSetUp(mock_test, mock_result)

        self.assertTrue(mock_class.__unittest_skip__)
        self.assertEqual(mock_class.__unittest_skip_why__, "kaboom")


class TestFunctional(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.startdir = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        if os.getcwd() != cls.startdir:
            os.chdir(cls.startdir)
        cls.startdir = None

    def setUp(self):
        self.args = copy.deepcopy(default_args)
        self.stream = StringIO()
        self.tmpdir = tempfile.mkdtemp()
        self.loader = GreenTestLoader()

    def tearDown(self):
        del(self.tmpdir)
        del(self.stream)

    def test_skip_in_setUpClass(self):
        """
        If SkipTest is raised in setUpClass, then the test gets skipped
        """
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        fh = open(os.path.join(sub_tmpdir, 'test_skipped.py'), 'w')
        fh.write(dedent(
            """
            import unittest
            class Skipper(unittest.TestCase):
                @classmethod
                def setUpClass(self):
                    raise unittest.SkipTest("the skip reason")
                def test_one(self):
                    pass
                def test_two(self):
                    pass
                import unittest
            """.format(os.getpid())))
        fh.close()
        os.chdir(sub_tmpdir)

        tests = self.loader.loadTargets('test_skipped')
        result = run(tests, self.stream, self.args)
        os.chdir(self.startdir)
        self.assertEqual(len(result.skipped), 2)
        self.assertEqual(self.stream.getvalue().count("the skip reason"), 2)
