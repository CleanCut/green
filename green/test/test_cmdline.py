from __future__ import unicode_literals
import logging
import os
import shutil
import sys
import tempfile
import unittest

from green import cmdline
from green import config
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
        saved_stdout = config.sys.stdout
        config.sys.stdout = self.gs
        self.addCleanup(setattr, config.sys, 'stdout', saved_stdout)


    def tearDown(self):
        del(self.gs)
        del(self.s)


    def test_notTesting(self):
        """
        We actually attempt running loadTargets (coverage test)
        """
        tmpdir = tempfile.mkdtemp()
        cwd = os.getcwd()
        os.chdir(tmpdir)
        sys.path.insert(0, cwd)
        config.sys.argv = ['', tmpdir]
        cmdline.main()
        os.chdir(cwd)
        del(sys.path[0])
        shutil.rmtree(tmpdir)


    def test_configFileDebug(self):
        """
        A debug message is output if a config file is loaded (coverage test)
        """
        tmpdir = tempfile.mkdtemp()
        filename = os.path.join(tmpdir, 'config')
        fh = open(filename, 'w')
        fh.write("debug = 2")
        fh.close()
        cmdline.sys.argv = ['', '-dd', '--config', filename]
        cmdline.main(testing=True)
        shutil.rmtree(tmpdir)


    def test_completionFile(self):
        """
        --completion-file causes a version string to be output
        """
        config.sys.argv = ['', '--completion-file']
        cmdline.main(testing=True)
        self.assertIn('shell_completion.sh', self.s.getvalue())



    def test_completions(self):
        """
        --completions returns completions (the loader module tests deeper)
        """
        cwd = os.getcwd()
        path = os.path.abspath(__file__)
        os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(path))))
        config.sys.argv = ['', '--completions', 'green']
        cmdline.main(testing=True)
        os.chdir(cwd)
        self.assertIn('green.test', self.s.getvalue())


    def test_options(self):
        """
        --options causes options to be output
        """
        cmdline.sys.argv = ['', '--options']
        cmdline.main(testing=True)
        self.assertIn('--options', self.s.getvalue())
        self.assertIn('--version', self.s.getvalue())


    def test_version(self):
        """
        --version causes a version string to be output
        """
        cmdline.sys.argv = ['', '--version']
        cmdline.main(testing=True)
        self.assertIn('Green', self.s.getvalue())
        self.assertIn('Python', self.s.getvalue())


    def test_debug(self):
        """
        --debug causes the log-level to be set to debug
        """
        config.sys.argv = ['', '--debug']
        saved_basicConfig = config.logging.basicConfig
        self.addCleanup(setattr, config.logging, 'basicConfig', saved_basicConfig)
        config.logging.basicConfig = MagicMock()
        cmdline.main(testing=True)
        config.logging.basicConfig.assert_called_with(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)9s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S")


    def test_disableTermcolor(self):
        """
        --notermcolor causes coverage of the line disabling termcolor
        """
        cmdline.sys.argv = ['', '--notermcolor']
        cmdline.main(testing=True)


    def test_disableWindowsSupport(self):
        """
        --disable-windows
        """
        cmdline.sys.argv = ['', '--disable-windows']
        cmdline.main(testing=True)


    def test_noCoverage(self):
        """
        The absence of coverage prompts a return code of 3
        """
        save_stdout = config.sys.stdout
        config.sys.stdout = MagicMock()
        save_coverage = config.coverage
        config.coverage = None
        config.sys.argv = ['', '--run-coverage']
        self.assertEqual(cmdline.main(), 3)
        config.coverage = save_coverage
        config.sys.stdout = save_stdout


    def test_noTestsCreatesEmptyTestSuite(self):
        """
        If loadTargets doesn't find any tests, an empty test suite is created.
        Coverage test, since loading the module inside the main function (due
        to coverage handling constraints) prevents injecting a mock.
        """
        cmdline.sys.argv = ['', '/tmp/non-existent/path']
        cmdline.main(testing=True)


    def test_import_cmdline_module(self):
        """
        The cmdline module can be imported
        """
        global reload
        try: # In Python 3.4+ reload is in importlib
            import importlib
            importlib.reload
            reload = importlib.reload
        except:
            try: # In Python 3.3 reload is in imp
                import imp
                imp.reload
                reload = imp.reload
            except:
                pass # Python 2.7's reload is builtin
        reload(cmdline)
