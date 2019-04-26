try:
    import configparser
except:
    import ConfigParser as configparser
import copy
from io import StringIO
import os
import shutil
import tempfile
import unittest

from green import config
from green.output import GreenStream


class ParseArguments(unittest.TestCase):

    def test_target(self):
        """
        The specified target gets parsed
        """
        config.sys.argv = ['', 'target1', 'target2']
        args = config.parseArguments()
        self.assertEqual(args.targets, ['target1', 'target2'])

    def test_absent(self):
        """
        Arguments not specified on the command-line are not present in the args
        object.
        """
        config.sys.argv = ['', '--debug']
        args = config.parseArguments()
        self.assertEqual(getattr(args, 'debug', 'not there'), True)
        self.assertEqual(getattr(args, 'verbose', 'not there'), 'not there')
        self.assertEqual(getattr(args, 'targets', 'not there'), 'not there')
        self.assertEqual(getattr(args, 'file_pattern', 'not there'),
                         'not there')


class ModifiedEnvironment(object):
    """
    I am a context manager that sets up environment variables for a test case.
    """

    def __init__(self, **kwargs):
        self.prev = {}
        self.excur = kwargs
        for k in kwargs:
            self.prev[k] = os.getenv(k)

    def __enter__(self):
        self.update_environment(self.excur)

    def __exit__(self, type, value, traceback):
        self.update_environment(self.prev)

    def update_environment(self, d):
        for k in d:
            if d[k] is None:
                if k in os.environ:
                    del os.environ[k]
            else:
                os.environ[k] = d[k]


class ConfigBase(unittest.TestCase):
    """
    I am an abstract base class that creates and destroys configuration files
    in a temporary directory with known values attached to self.
    """

    def _write_file(self, path, lines):
        f = open(path, 'w')
        f.writelines([x + "\n" for x in lines])
        f.close()

    def setUp(self):
        self.tmpd = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpd)
        # Set CWD to known empty directory so we don't pick up some other .green
        # file from the CWD tests are actuall run from.
        save_cwd = os.getcwd()
        self.addCleanup(os.chdir, save_cwd)
        cwd_dir = os.path.join(self.tmpd, 'cwd')
        os.mkdir(cwd_dir)
        os.chdir(cwd_dir)
        # This represents the $HOME config file, and doubles for the current
        # working directory config file if we set CWD to self.tmpd
        self.default_filename = os.path.join(self.tmpd, ".green")
        self.default_logging = False
        self.default_version = False
        self.default_failfast = True
        self.default_termcolor = True
        self._write_file(self.default_filename,
                         ["# this is a test config file for green",
                          "logging = {}".format(str(self.default_logging)),
                          "version = {}".format(str(self.default_version)),
                          "omit-patterns = {}".format(self.default_filename),
                          "failfast = {}".format(str(self.default_failfast)),
                          "termcolor = {}".format(str(self.default_termcolor)),
                          ])
        self.env_filename = os.path.join(self.tmpd, "green.env")
        self.env_logging = True
        self.env_no_skip_report = False
        self._write_file(self.env_filename,
                         ["# this is a test config file for green",
                          "logging = {}".format(str(self.env_logging)),
                          "omit-patterns = {}".format(self.env_filename),
                          "no-skip-report = {}".format(self.env_no_skip_report),
                          ])
        self.cmd_filename = os.path.join(self.tmpd, "green.cmd")
        self.cmd_logging = False
        self.cmd_run_coverage = False
        self._write_file(self.cmd_filename,
                         ["# this is a test config file for green",
                          "logging = {}".format(str(self.cmd_logging)),
                          "omit-patterns = {}".format(self.cmd_filename),
                          "run-coverage = {}".format(self.cmd_run_coverage),
                          ])
        self.setup_filename = os.path.join(cwd_dir, "setup.cfg")
        self.setup_failfast = False
        self.setup_verbose = 3
        self._write_file(self.setup_filename,
                         ["[green]",
                          "failfast = {}".format(str(self.setup_failfast)),
                          "verbose = {}".format(str(self.setup_verbose))
                         ])


class TestConfig(ConfigBase):
    """
    All variations of config file parsing works as expected.
    """

    def test_cmd_env_nodef_nosetup(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG is set, $HOME/.green does not
            exist, setup.cfg does not exist
        Result: load --config
        """
        os.unlink(self.default_filename)
        os.remove(self.setup_filename)
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename,
                                 HOME=self.tmpd):
            cfg = config.getConfig(self.cmd_filename)
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.cmd_filename,          cfg.get("green", "omit-patterns"))
            ae(self.cmd_run_coverage,      cfg.getboolean("green", "run-coverage"))
            ae(self.cmd_logging,           cfg.getboolean("green", "logging"))
            ae(self.env_no_skip_report,    cfg.getboolean("green", "no-skip-report"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "version")
            ar(configparser.NoOptionError, cfg.getboolean, "green", "verbose")

    def test_cmd_noenv_def_nosetup(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG unset, $HOME/.green exists,
            setup.cfg does not exist
        Result: load --config
        """
        os.unlink(self.env_filename)
        os.remove(self.setup_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.getConfig(self.cmd_filename)
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.cmd_filename,          cfg.get("green", "omit-patterns"))
            ae(self.cmd_run_coverage,      cfg.getboolean("green", "run-coverage"))
            ae(self.cmd_logging,           cfg.getboolean("green", "logging"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "no-skip-report")
            ae(self.default_version,       cfg.getboolean("green", "version"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "verbose")

    def test_cmd_noenv_nodef_nosetup(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG unset, $HOME/.green does not
            exist, setup.cfg does not exist
        Result: load --config
        """
        os.unlink(self.env_filename)
        os.unlink(self.default_filename)
        os.remove(self.setup_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.getConfig(self.cmd_filename)
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.cmd_filename,          cfg.get("green", "omit-patterns"))
            ae(self.cmd_run_coverage,      cfg.getboolean("green", "run-coverage"))
            ae(self.cmd_logging,           cfg.getboolean("green", "logging"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "no-skip-report")
            ar(configparser.NoOptionError, cfg.getboolean, "green", "version")
            ar(configparser.NoOptionError, cfg.getboolean, "green", "verbose")

    def test_nocmd_env_cwd(self):
        """
        Setup: no --config option, $GREEN_CONFIG is set, .green in local dir,
        Result: load $GREEN_CONFIG
        """
        os.chdir(self.tmpd) # setUp is already set to restore us to our pre-testing cwd
        os.unlink(self.cmd_filename)
        os.remove(self.setup_filename)
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename,
                                 HOME=self.tmpd):
            cfg = config.getConfig()
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.default_filename,      cfg.get("green", "omit-patterns"))
            ar(configparser.NoOptionError, cfg.get, "green", "run-coverage")
            ae(self.default_logging,           cfg.getboolean("green", "logging"))
            ae(self.env_no_skip_report,    cfg.getboolean("green", "no-skip-report"))
            ae(self.default_version,       cfg.getboolean("green", "version"))
            ar(configparser.NoOptionError, cfg.getint, "green", "verbose")

    def test_nocmd_env_def_nosetup(self):
        """
        Setup: no --config option, $GREEN_CONFIG is set, $HOME/.green exists,
            setup.cfg does not exist
        Result: load $GREEN_CONFIG
        """
        os.unlink(self.cmd_filename)
        os.remove(self.setup_filename)
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename,
                                 HOME=self.tmpd):
            cfg = config.getConfig()
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.env_filename,          cfg.get("green", "omit-patterns"))
            ar(configparser.NoOptionError, cfg.get, "green", "run-coverage")
            ae(self.env_logging,           cfg.getboolean("green", "logging"))
            ae(self.env_no_skip_report,    cfg.getboolean("green", "no-skip-report"))
            ae(self.default_version,       cfg.getboolean("green", "version"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "verbose")

    def test_nocmd_env_nodef_nosetup(self):
        """
        Setup: no --config option, $GREEN_CONFIG is set, $HOME/.green does not
            exist, setup.cfg does not exist
        Result: load $GREEN_CONFIG
        """
        os.unlink(self.cmd_filename)
        os.unlink(self.default_filename)
        os.remove(self.setup_filename)
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename,
                                 HOME=self.tmpd):
            cfg = config.getConfig()
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.env_filename,          cfg.get("green", "omit-patterns"))
            ar(configparser.NoOptionError, cfg.get, "green", "run-coverage")
            ae(self.env_logging,           cfg.getboolean("green", "logging"))
            ae(self.env_no_skip_report,    cfg.getboolean("green", "no-skip-report"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "version")
            ar(configparser.NoOptionError, cfg.getboolean, "green", "verbose")

    def test_nocmd_noenv_def_nosetup(self):
        """
        Setup: no --config option, $GREEN_CONFIG unset, $HOME/.green exists,
            setup.cfg does not exist
        Result: load $HOME/.green
        """
        os.unlink(self.cmd_filename)
        os.unlink(self.env_filename)
        os.remove(self.setup_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.getConfig()
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.default_filename,      cfg.get("green", "omit-patterns"))
            ar(configparser.NoOptionError, cfg.get, "green", "run-coverage")
            ae(self.default_logging,       cfg.getboolean("green", "logging"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "no-skip-report")
            ae(self.default_version,       cfg.getboolean("green", "version"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "verbose")

    def test_nocmd_noenv_nodef_nosetup(self):
        """
        Setup: no --config option, $GREEN_CONFIG unset, no $HOME/.green,
            setup.cfg does not exist
        Result: empty config
        """
        os.unlink(self.default_filename)
        os.unlink(self.env_filename)
        os.unlink(self.cmd_filename)
        os.remove(self.setup_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.getConfig()
            ae = self.assertEqual
            ar = self.assertRaises
            ae([], cfg.sections())
            ar(configparser.NoSectionError, cfg.get, "green", "omit-patterns")
            ar(configparser.NoSectionError, cfg.get, "green", "run-coverage")
            ar(configparser.NoSectionError, cfg.get, "green", "logging")
            ar(configparser.NoSectionError, cfg.get, "green", "no-skip-report")
            ar(configparser.NoSectionError, cfg.get, "green", "version")
            ar(configparser.NoSectionError, cfg.get, "green", "verbose")

    def test_cmd_env_nodef_setup(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG is set, $HOME/.green does not
            exist, setup.cfg exists
        Result: load --config
        """
        os.unlink(self.default_filename)
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename,
                                 HOME=self.tmpd):
            cfg = config.getConfig(self.cmd_filename)
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.cmd_filename,          cfg.get("green", "omit-patterns"))
            ae(self.cmd_run_coverage,      cfg.getboolean("green", "run-coverage"))
            ae(self.cmd_logging,           cfg.getboolean("green", "logging"))
            ae(self.env_no_skip_report,    cfg.getboolean("green", "no-skip-report"))
            ae(self.setup_verbose,         cfg.getint("green", "verbose"))
            ae(self.setup_failfast,        cfg.getboolean("green", "failfast"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "version")

    def test_cmd_noenv_def_setup(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG unset, $HOME/.green exists,
            setup.cfg exists
        Result: load --config
        """
        os.unlink(self.env_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.getConfig(self.cmd_filename)
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.cmd_filename,          cfg.get("green", "omit-patterns"))
            ae(self.cmd_run_coverage,      cfg.getboolean("green", "run-coverage"))
            ae(self.cmd_logging,           cfg.getboolean("green", "logging"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "no-skip-report")
            ae(self.default_version,       cfg.getboolean("green", "version"))
            ae(self.setup_verbose,         cfg.getint("green", "verbose"))
            ae(self.setup_failfast,        cfg.getboolean("green", "failfast"))

    def test_cmd_noenv_nodef_setup(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG unset, $HOME/.green does not exist,
            setup.cfg exists
        Result: load --config
        """
        os.unlink(self.env_filename)
        os.unlink(self.default_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.getConfig(self.cmd_filename)
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.cmd_filename,          cfg.get("green", "omit-patterns"))
            ae(self.cmd_run_coverage,      cfg.getboolean("green", "run-coverage"))
            ae(self.cmd_logging,           cfg.getboolean("green", "logging"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "no-skip-report")
            ar(configparser.NoOptionError, cfg.getboolean, "green", "version")
            ae(self.setup_verbose,         cfg.getint("green", "verbose"))
            ae(self.setup_failfast,        cfg.getboolean("green", "failfast"))

    def test_nocmd_env_def_setup(self):
        """
        Setup: no --config option, $GREEN_CONFIG is set, $HOME/.green exists,
            setup.cfg exists
        Result: load $GREEN_CONFIG
        """
        os.unlink(self.cmd_filename)
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename,
                                 HOME=self.tmpd):
            cfg = config.getConfig()
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.env_filename,          cfg.get("green", "omit-patterns"))
            ar(configparser.NoOptionError, cfg.get, "green", "run-coverage")
            ae(self.env_logging,           cfg.getboolean("green", "logging"))
            ae(self.env_no_skip_report,    cfg.getboolean("green", "no-skip-report"))
            ae(self.default_version,       cfg.getboolean("green", "version"))
            ae(self.setup_verbose,         cfg.getint("green", "verbose"))
            ae(self.setup_failfast,        cfg.getboolean("green", "failfast"))

    def test_nocmd_env_nodef_setup(self):
        """
        Setup: no --config option, $GREEN_CONFIG is set, $HOME/.green does not
            exist, setup.cfg exists
        Result: load $GREEN_CONFIG
        """
        os.unlink(self.cmd_filename)
        os.unlink(self.default_filename)
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename,
                                 HOME=self.tmpd):
            cfg = config.getConfig()
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.env_filename,          cfg.get("green", "omit-patterns"))
            ar(configparser.NoOptionError, cfg.get, "green", "run-coverage")
            ae(self.env_logging,           cfg.getboolean("green", "logging"))
            ae(self.env_no_skip_report,    cfg.getboolean("green", "no-skip-report"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "version")
            ae(self.setup_verbose,         cfg.getint("green", "verbose"))
            ae(self.setup_failfast,        cfg.getboolean("green", "failfast"))

    def test_nocmd_noenv_def_setup(self):
        """
        Setup: no --config option, $GREEN_CONFIG unset, $HOME/.green exists,
            setup.cfg exists
        Result: load $HOME/.green
        """
        os.unlink(self.cmd_filename)
        os.unlink(self.env_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.getConfig()
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.default_filename,      cfg.get("green", "omit-patterns"))
            ar(configparser.NoOptionError, cfg.get, "green", "run-coverage")
            ae(self.default_logging,       cfg.getboolean("green", "logging"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "no-skip-report")
            ae(self.default_version,       cfg.getboolean("green", "version"))
            ae(self.setup_verbose,         cfg.getint("green", "verbose"))
            ae(self.setup_failfast,        cfg.getboolean("green", "failfast"))

    def test_nocmd_noenv_nodef_setup(self):
        """
        Setup: no --config option, $GREEN_CONFIG unset, no $HOME/.green,
            setup.cfg exists
        Result: empty config
        """
        os.unlink(self.default_filename)
        os.unlink(self.env_filename)
        os.unlink(self.cmd_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.getConfig()
            ae = self.assertEqual
            ar = self.assertRaises
            ae(self.setup_verbose, cfg.getint("green", "verbose"))
            ae(self.setup_failfast, cfg.getboolean("green", "failfast"))
            ar(configparser.NoOptionError, cfg.get, "green", "omit-patterns")
            ar(configparser.NoOptionError, cfg.get, "green", "run-coverage")
            ar(configparser.NoOptionError, cfg.get, "green", "logging")
            ar(configparser.NoOptionError, cfg.get, "green", "no-skip-report")
            ar(configparser.NoOptionError, cfg.get, "green", "version")





class TestMergeConfig(ConfigBase):
    """
    Merging config files and command-line arguments works as expected.
    """

    def test_overwrite(self):
        """
        Non-default command-line argument values overwrite config values.
        """
        # This config environment should set the values we look at to False and
        # a filename in omit-patterns
        s = StringIO()
        gs = GreenStream(s)
        saved_stdout = config.sys.stdout
        config.sys.stdout = gs
        self.addCleanup(setattr, config.sys, 'stdout', saved_stdout)
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename,
                                 HOME=self.tmpd):
            new_args = copy.deepcopy(config.default_args)

            new_args.omit_patterns  = 'omitstuff'
            new_args.run_coverage   = True
            new_args.logging        = True
            new_args.no_skip_report = True
            new_args.version        = True

            new_args.config = self.cmd_filename
            computed_args = config.mergeConfig(new_args, testing=True)

            self.assertEqual(computed_args.omit_patterns,  'omitstuff')
            self.assertEqual(computed_args.run_coverage,   new_args.run_coverage)
            self.assertEqual(computed_args.logging,        new_args.logging)
            self.assertEqual(computed_args.no_skip_report, new_args.no_skip_report)
            self.assertEqual(computed_args.version,        new_args.version)

    def test_no_overwrite(self):
        """
        Default unspecified command-line args do not overwrite config values.
        """
        # This config environment should set logging to True
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename, HOME=""):
            # The default for logging in arguments is False
            da = copy.deepcopy(config.default_args)
            del(da.logging)
            computed_args = config.mergeConfig(da, testing=True)
            self.assertEqual(computed_args.logging, True)

    def test_specified_command_line(self):
        """
        Specified command-line arguments always overwrite config file values
        """
        with ModifiedEnvironment(HOME=self.tmpd):
            new_args = copy.deepcopy(config.default_args)
            new_args.failfast = True  # same as config, for sanity
            new_args.logging = True  # different than config, not default
            del(new_args.version)  # Not in arguments, should get config value
            new_args.termcolor = False  # override config, set back to default
            computed_args = config.mergeConfig(new_args, testing=True)
            self.assertEqual(computed_args.failfast, True)
            self.assertEqual(computed_args.logging, True)
            self.assertEqual(computed_args.version, False)
            self.assertEqual(computed_args.termcolor, False)

    def test_targets(self):
        """
        The targets passed in make it through mergeConfig, and the specified
        target gets parsed
        """
        config.sys.argv = ['', 'target1', 'target2']
        args = config.parseArguments()
        args = config.mergeConfig(args)
        self.assertEqual(args.targets, ['target1', 'target2'])

    def test_forgotToUpdateMerge(self):
        """
        mergeConfig raises an exception for unknown cmdline args
        """
        orig_args = copy.deepcopy(config.default_args)
        self.addCleanup(setattr, config, 'default_args', orig_args)
        config.default_args.new_option = True

        new_args = copy.deepcopy(config.default_args)

        self.assertRaises(NotImplementedError, config.mergeConfig, new_args,
                          testing=True)
