from __future__ import unicode_literals

import argparse
import contextlib
import sys
import unittest

try:
    from setuptools.dist import Distribution
except ImportError:
    from distutil.dist import Distribution

try:
    from mock import patch, MagicMock, call
except:
    from unittest.mock import patch, MagicMock, call

from green import command
from green.config import StoreOpt


class TestCommand(unittest.TestCase):


    @contextlib.contextmanager
    def environ(self, setup_cfg=None, *args, **variables):

        args = ['green'] + list(args)

        if setup_cfg is not None:
            parser = ConfigParser()
            parser.add_section('green')
            for k, v in setup_cfg.items():
                parser.set('green', k, str(v))
            with open('setup.cfg', 'w') as f:
                parser.write(f)

        yield Distribution({'script_name': 'setup.py',
                            'script_args': args or ['green']})

        #finally:
        if os.path.isfile('setup.cfg'):
            os.remove('setup.cfg')

    def test_get_user_options(self):
        # Check the user options contain some of the
        # actual command line options
        options = command.get_user_options()

        self.assertIn(
            ("options", None,
             "Output all options.  Used by bash- and zsh-completion."),
            options
        )

        self.assertIn(
            ('file-pattern=', 'p',
             'Pattern to match test files. Default is test*.py'),
            options
        )

    def test_get_user_options_setup_py(self):
        """
        When get_user_options() is called by 'python setup.py --help-commands',
        it returns [] early and doesn't crash.
        """
        sys.argv.append('--help-commands')
        self.addCleanup(lambda: sys.argv.pop())

        self.assertEqual(command.get_user_options(), [])

    @patch('green.command.parseArguments')
    def test_get_user_options_dynamic(self, parseArguments):
        # Check the user options are generated after
        # the command line options created in green.cmdline.parseArguments
        store_opt = StoreOpt()
        argparser = argparse.ArgumentParser()
        store_opt(argparser.add_argument("-s", "--something", help="Something"))
        store_opt(argparser.add_argument("--else", help="Else"))
        store_opt(argparser.add_argument("-a", "--again", action="store_true", help="Again"))

        args = argparser.parse_args([])
        args.parser = argparser
        args.store_opt = store_opt
        parseArguments.return_value = args

        options = command.get_user_options()

        self.assertEqual(options, [
            ('something=', 's', 'Something'),
            ('else=', None, 'Else'),
            ('again', 'a', 'Again'),
        ])

    def test_initialize_options(self):
        d =  Distribution({'script_name': 'setup.py',
                           'script_args': ['green']})

        cmd = command.green(d)
        for attr in ['completion_file', 'clear_omit', 'debug', 'processes']:
            self.assertTrue(hasattr(cmd, attr), attr)

    @patch('green.command.main', return_value=0)
    def test_run(self, main):
        d =  Distribution({'script_name': 'setup.py',
                           'script_args': ['green'],
                           'test_suite': 'green.test.test_version'})

        cmd = command.green(d)
        cmd.run()
        main.assert_called_once_with(['green.test.test_version'])

    @patch('green.command.main', return_value=125)
    def test_run_exits(self, main):
        d =  Distribution({'script_name': 'setup.py',
                           'script_args': ['green']})

        cmd = command.green(d)
        with self.assertRaises(SystemExit) as se:
            cmd.run()
        self.assertEqual(se.exception.code, 125)

    @patch('green.command.main', return_value=0)
    def test_requires(self, main):
        d = Distribution({'script_name': 'setup.py',
                          'script_args': ['green'],
                          'install_requires': ['six'],
                          'tests_require': ['mock', 'unittest2']})
        d.fetch_build_eggs = MagicMock()
        cmd = command.green(d)
        cmd.run()

        d.fetch_build_eggs.assert_has_calls([
            call(['six']),
            call(['mock', 'unittest2']),
        ])
