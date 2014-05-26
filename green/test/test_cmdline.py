from __future__ import unicode_literals
import logging
import sys
import unittest

from green import cmdline
from green.output import GreenStream

try:
    from io import StringIO
except:
    from StringIO import StringIO

try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock



class TestMain(unittest.TestCase):


    def setUp(self):
        self.s = StringIO()
        self.gs = GreenStream(self.s)
        self.saved_stdout = sys.stdout
        self.saved_stderr = cmdline.sys.stderr
        self.saved_argv = sys.argv
        sys.stdout = self.gs
        cmdline.sys.stderr = self.gs


    def tearDown(self):
        sys.stdout = self.saved_stdout
        cmdline.sys.stderr = self.saved_stderr
        sys.argv = self.saved_argv
        del(self.gs)
        del(self.s)
        del(self.saved_stderr)
        del(self.saved_stdout)

    def test_optVersion(self):
        "--version causes a version string to be output"
        cmdline.sys.argv = ['', '--version']
        cmdline.main(testing=True)
        self.assertIn('Green', self.s.getvalue())
        self.assertIn('Python', self.s.getvalue())


    def test_debug(self):
        "--debug causes the log-level to be set to debug"
        cmdline.sys.argv = ['', '--debug']
        saved_basicConfig = cmdline.logging.basicConfig
        cmdline.logging.basicConfig = MagicMock()
        cmdline.main(testing=True)
        cmdline.logging.basicConfig.assert_called_with(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)9s %(message)s")
        cmdline.logging.basicConfig = saved_basicConfig


    def test_disableTermcolor(self):
        "--notermcolor causes coverage of the line disabling termcolor"
        cmdline.sys.argv = ['', '--notermcolor']
        cmdline.main(testing=True)


    def test_noCoverage(self):
        "The absence of coverage prompts a return code of 3"
        save_stderr = cmdline.sys.stderr
        cmdline.sys.stderr = MagicMock()
        save_coverage = cmdline.coverage
        cmdline.coverage = None
        cmdline.sys.argv = ['', '--run-coverage']
        self.assertEqual(cmdline.main(), 3)
        cmdline.coverage = save_coverage
        cmdline.sys.stderr = save_stderr


    def test_coverage(self):
        "If coverage and --run-coverage, then coverage is started"
        save_coverage = cmdline.coverage
        cmdline.coverage = MagicMock()
        cmdline.sys.argv = ['', '--run-coverage']
        cmdline.main(testing=True)
        cmdline.coverage.coverage.assert_called_with()
        cmdline.coverage = save_coverage


    def test_noTestsCreatesEmptyTestSuite(self):
        "If getTests doesn't find any tests, an empty test suite is created"
        save_TestSuite = cmdline.unittest.suite.TestSuite
        cmdline.unittest.suite.TestSuite = MagicMock()
        cmdline.sys.argv = ['', '/tmp/non-existent/path']
        cmdline.main(testing=True)
        cmdline.unittest.suite.TestSuite.assert_called_with()
        cmdline.unittest.suite.TestSuite = save_TestSuite


    def test_omit(self):
        "Omit pattern gets parsed"
        save_coverage = cmdline.coverage
        cmdline.coverage = MagicMock()
        cov = MagicMock()
        cmdline.coverage.coverage.return_value = cov
        cmdline.sys.argv = ['', '--run-coverage', '--omit', 'a,b']
        cmdline.main(testing=True)
        self.assertEqual(cov.report.mock_calls[0][2]['omit'], ['a', 'b'])
        cmdline.coverage = save_coverage


