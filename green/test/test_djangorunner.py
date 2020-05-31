from __future__ import unicode_literals
from argparse import Namespace
from argparse import ArgumentParser
from io import StringIO
import sys
import unittest

try:
    from unittest.mock import MagicMock, patch
except:
    from mock import MagicMock, patch

from green import djangorunner
from green.config import mergeConfig


class TestDjangoMissing(unittest.TestCase):
    def test_importError(self):
        """
        Raises ImportError if Django is not available
        """
        self.assertRaises(ImportError, djangorunner.django_missing)


class TestDjangoRunner(unittest.TestCase):
    def setUp(self):
        try:
            djangorunner.DjangoRunner()
        except ImportError:
            raise unittest.SkipTest("Django is not installed")
        saved_stdout = sys.stdout
        self.stream = StringIO()
        sys.stdout = self.stream
        self.addCleanup(setattr, sys, "stdout", saved_stdout)

    def test_run_testsWithLabel(self):
        """
        Labeled tests run okay
        """
        dr = djangorunner.DjangoRunner()
        dr.setup_test_environment = MagicMock()
        dr.setup_databases = MagicMock()
        dr.teardown_databases = MagicMock()
        dr.teardown_test_environment = MagicMock()

        dr.run_tests(("green.test.test_version",), testing=True)

        self.assertIn("OK", self.stream.getvalue())

    def test_run_testsWithoutLabel(self):
        """
        Not passing in a label causes the targets to be ['.']
        """
        dr = djangorunner.DjangoRunner()
        dr.setup_test_environment = MagicMock()
        dr.setup_databases = MagicMock()
        dr.teardown_databases = MagicMock()
        dr.teardown_test_environment = MagicMock()

        with patch.object(dr.loader, "loadTargets") as mock_loadTargets:
            dr.run_tests((), testing=True)

        mock_loadTargets.assert_called_with(["."])
        self.assertIn("No Tests Found", self.stream.getvalue())

    def test_run_testsWithBadInput(self):
        """
        Bad input causes a ValueError to be raised
        """
        dr = djangorunner.DjangoRunner()
        dr.setup_test_environment = MagicMock()
        dr.setup_databases = MagicMock()

        self.assertRaises(ValueError, dr.run_tests, None, True)

    @patch("green.djangorunner.GreenTestSuite")
    @patch("green.djangorunner.run")
    def test_run_noTests(self, mock_run, mock_GreenTestSuite):
        """
        If no tests are found, we create an empty test suite and run it.
        """
        dr = djangorunner.DjangoRunner()

        dr.setup_test_environment = MagicMock()
        dr.setup_databases = MagicMock()
        dr.teardown_databases = MagicMock()
        dr.teardown_test_environment = MagicMock()

        mock_GreenTestSuite.return_value = 123

        with patch.object(dr.loader, "loadTargets", return_value=None):
            dr.run_tests((), testing=True)

        self.assertEqual(mock_run.call_args[0][0], 123)

    @patch("green.djangorunner.mergeConfig")
    @patch("green.djangorunner.GreenTestSuite")
    @patch("green.djangorunner.run")
    def test_run_coverage(self, mock_run, mock_GreenTestSuite, mock_mergeConfig):
        """
        If no tests are found, we create an empty test suite and run it.
        """
        args = mergeConfig(Namespace())
        args.run_coverage = True
        args.cov = MagicMock()
        mock_mergeConfig.return_value = args
        dr = djangorunner.DjangoRunner()

        dr.setup_test_environment = MagicMock()
        dr.setup_databases = MagicMock()
        dr.teardown_databases = MagicMock()
        dr.teardown_test_environment = MagicMock()

        mock_GreenTestSuite.return_value = 123

        with patch.object(dr.loader, "loadTargets", return_value=None):
            dr.run_tests((), testing=True)

        self.assertEqual(mock_run.call_args[0][0], 123)

    def test_check_verbosity_argument_recognised(self):
        """
        Ensure that the python manage.py test command
        recognises the --green-verbosity flag
        """
        dr = djangorunner.DjangoRunner()
        dr.setup_test_environment = MagicMock()
        dr.setup_databases = MagicMock()
        dr.teardown_databases = MagicMock()
        dr.teardown_test_environment = MagicMock()
        from django.core.management.commands.test import Command as TestCommand

        test_command = TestCommand()
        test_command.test_runner = "green.djangorunner.DjangoRunner"
        parser = ArgumentParser()
        test_command.add_arguments(parser)
        args = parser.parse_args()
        self.assertIn("verbose", args)

    def test_check_default_verbosity(self):
        """
        If no verbosity is passed, default value is set
        """
        dr = djangorunner.DjangoRunner()
        dr.setup_test_environment = MagicMock()
        dr.setup_databases = MagicMock()
        dr.teardown_databases = MagicMock()
        dr.teardown_test_environment = MagicMock()
        from django.core.management.commands.test import Command as TestCommand

        test_command = TestCommand()
        test_command.test_runner = "green.djangorunner.DjangoRunner"
        parser = ArgumentParser()
        test_command.add_arguments(parser)
        args = parser.parse_args()
        self.assertEqual(args.verbose, -1)

    def test_run_with_verbosity_flag(self):
        """
        Tests should run fine if verbosity is passed
        through CLI flag
        """
        dr = djangorunner.DjangoRunner()
        dr.setup_test_environment = MagicMock()
        dr.setup_databases = MagicMock()
        dr.teardown_databases = MagicMock()
        dr.teardown_test_environment = MagicMock()
        dr.verbose = 2
        saved_loadTargets = dr.loader.loadTargets
        dr.loader.loadTargets = MagicMock()
        self.addCleanup(setattr, dr.loader, "loadTargets", saved_loadTargets)
        self.assertEqual((dr.run_tests((), testing=True)), 0)
