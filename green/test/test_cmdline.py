from __future__ import unicode_literals
from io import StringIO
import logging
import os
from os.path import isfile, join
import shutil
import sys
import tempfile
import unittest

from green import cmdline
from green import config
from green.output import GreenStream

try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock


class TestMain(unittest.TestCase):
    def setUp(self):
        self.s = StringIO()
        self.gs = GreenStream(self.s)
        saved_stdout = config.sys.stdout
        config.sys.stdout = self.gs
        self.addCleanup(setattr, config.sys, "stdout", saved_stdout)

    def tearDown(self):
        del self.gs
        del self.s

    def test_notTesting(self):
        """
        We actually attempt running loadTargets (coverage test)
        """
        tmpdir = tempfile.mkdtemp()
        cwd = os.getcwd()
        os.chdir(tmpdir)
        sys.path.insert(0, cwd)
        argv = [tmpdir]
        cmdline.main(argv)
        os.chdir(cwd)
        del sys.path[0]
        shutil.rmtree(tmpdir)

    def test_configFileDebug(self):
        """
        A debug message is output if a config file is loaded (coverage test)
        """
        tmpdir = tempfile.mkdtemp()
        filename = os.path.join(tmpdir, "config")
        fh = open(filename, "w")
        fh.write("debug = 2")
        fh.close()
        argv = ["-dd", "--config", filename]
        cmdline.main(argv, testing=True)
        shutil.rmtree(tmpdir)

    def test_completionFile(self):
        """
        --completion-file causes a version string to be output
        """
        argv = ["--completion-file"]
        cmdline.main(argv, testing=True)
        self.assertIn("shell_completion.sh", self.s.getvalue())

    def test_completions(self):
        """
        --completions returns completions (the loader module tests deeper)
        """
        cwd = os.getcwd()
        path = os.path.abspath(__file__)
        os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(path))))
        argv = ["--completions", "green"]
        cmdline.main(argv, testing=True)
        os.chdir(cwd)
        self.assertIn("green.test", self.s.getvalue())

    def test_options(self):
        """
        --options causes options to be output
        """
        argv = ["--options"]
        cmdline.main(argv, testing=True)
        self.assertIn("--options", self.s.getvalue())
        self.assertIn("--version", self.s.getvalue())

    def test_version(self):
        """
        --version causes a version string to be output
        """
        argv = ["--version"]
        cmdline.main(argv, testing=True)
        self.assertIn("Green", self.s.getvalue())
        self.assertIn("Python", self.s.getvalue())

    def test_debug(self):
        """
        --debug causes the log-level to be set to debug
        """
        argv = ["--debug"]
        saved_basicConfig = config.logging.basicConfig
        self.addCleanup(setattr, config.logging, "basicConfig", saved_basicConfig)
        config.logging.basicConfig = MagicMock()
        cmdline.main(argv, testing=True)
        config.logging.basicConfig.assert_called_with(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)9s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def test_disableTermcolor(self):
        """
        --notermcolor causes coverage of the line disabling termcolor
        """
        argv = ["--notermcolor"]
        cmdline.main(argv, testing=True)

    def test_disableWindowsSupport(self):
        """
        --disable-windows
        """
        argv = ["--disable-windows"]
        cmdline.main(argv, testing=True)

    def test_noTestsCreatesEmptyTestSuite(self):
        """
        If loadTargets doesn't find any tests, an empty test suite is created.
        Coverage test, since loading the module inside the main function (due
        to coverage handling constraints) prevents injecting a mock.
        """
        argv = ["", "/tmp/non-existent/path"]
        cmdline.main(argv, testing=True)

    def test_import_cmdline_module(self):
        """
        The cmdline module can be imported
        """
        global reload
        try:  # In Python 3 reload is in importlib
            import importlib

            importlib.reload
            reload = importlib.reload
        except:
            pass  # Python 2.7's reload is builtin
        reload(cmdline)

    def test_generate_junit_test_report(self):
        """
        Test that a report is generated when we use the '--junit-report' option.
        """
        tmpdir = tempfile.mkdtemp()
        report = join(tmpdir, "test_report.xml")
        self.assertFalse(isfile(report))

        argv = ["--junit-report", report]
        cmdline.main(argv, testing=True)

        self.assertTrue(isfile(report))
        shutil.rmtree(tmpdir)
