from __future__ import unicode_literals
try:
    from io import StringIO
except:
    from StringIO import StringIO
import sys
import unittest
try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock

from green import djangorunner


class TestDjangoMissing(unittest.TestCase):


    def test_importError(self):
        self.assertRaises(ImportError, djangorunner.django_missing)




class TestDjangoRunner(unittest.TestCase):


    def setUp(self):
        try:
            djangorunner.DjangoRunner()
        except ImportError:
            raise unittest.SkipTest("Django is not installed")
        self.saved_stdout = sys.stdout
        self.stream = StringIO()
        sys.stdout = self.stream


    def tearDown(self):
        sys.stdout = self.saved_stdout


    def test_run_testsWithLabel(self):
        dr = djangorunner.DjangoRunner()
        dr.setup_test_environment    = MagicMock()
        dr.setup_databases           = MagicMock()
        dr.teardown_databases        = MagicMock()
        dr.teardown_test_environment = MagicMock()

        dr.run_tests(('green.test.test_version',))

        self.assertIn('OK', self.stream.getvalue())


    def test_run_testsWithoutLabel(self):
        "Not passing in a label causes the targets to be ['.']"
        dr = djangorunner.DjangoRunner()
        dr.setup_test_environment    = MagicMock()
        dr.setup_databases           = MagicMock()
        dr.teardown_databases        = MagicMock()
        dr.teardown_test_environment = MagicMock()

        saved_loadTargets = djangorunner.loadTargets
        djangorunner.loadTargets = MagicMock()

        dr.run_tests(())
        djangorunner.loadTargets.assert_called_with(['.'])
        djangorunner.loadTargets = saved_loadTargets
        self.assertIn('No Tests Found', self.stream.getvalue())


    def test_run_testsWithBadInput(self):
        "Bad input causes a ValueError to be raised"
        dr = djangorunner.DjangoRunner()
        dr.setup_test_environment    = MagicMock()
        dr.setup_databases           = MagicMock()

        self.assertRaises(ValueError, dr.run_tests, None)
