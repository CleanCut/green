try:
    import configparser
except:
    import ConfigParser as configparser
import copy
try:
    from io import StringIO
except:
    from StringIO import StringIO
import os
import shutil
import tempfile
import unittest

from green import config
from green.output import GreenStream



class ParseArguments(unittest.TestCase):


    def test_target(self):
        "The specified target gets parsed"
        config.sys.argv = ['', 'target1', 'target2']
        args = config.parseArguments()
        self.assertEqual(args.targets, ['target1', 'target2'])



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
        self.default_filename = os.path.join(self.tmpd, ".green")
        self.default_logging = False
        self.default_version = False
        self._write_file(self.default_filename,
                        ["# this is a test config file for green",
                         "logging = {}".format(str(self.default_logging)),
                         "version = {}".format(str(self.default_version)),
                         "omit = {}".format(self.default_filename),
                         ])
        self.env_filename = os.path.join(self.tmpd, "green.env")
        self.env_logging = True
        self.env_html = False
        self._write_file(self.env_filename,
                        ["# this is a test config file for green",
                         "logging = {}".format(str(self.env_logging)),
                         "omit = {}".format(self.env_filename),
                         "html = {}".format(self.env_html),
                         ])
        self.cmd_filename = os.path.join(self.tmpd, "green.cmd")
        self.cmd_logging = False
        self.cmd_run_coverage = False
        self._write_file(self.cmd_filename,
                        ["# this is a test config file for green",
                         "logging = {}".format(str(self.cmd_logging)),
                         "omit = {}".format(self.cmd_filename),
                         "run-coverage = {}".format(self.cmd_run_coverage),
                         ])


    def tearDown(self):
        shutil.rmtree(self.tmpd)



class TestConfig(ConfigBase):
    """
    All variations of config file parsing works as expected.
    """


    def test_cmd_env_def(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG is set, $HOME/.green exists
        Result: load --config
        """
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename, HOME=self.tmpd):
            cfg = config.getConfig(self.cmd_filename)
            ae = self.assertEqual
            ae(["green"],             cfg.sections())
            ae(self.cmd_filename,     cfg.get("green", "omit"))
            ae(self.cmd_run_coverage, cfg.getboolean("green", "run-coverage"))
            ae(self.cmd_logging,      cfg.getboolean("green", "logging"))
            ae(self.env_html,         cfg.getboolean("green", "html"))
            ae(self.default_version,  cfg.getboolean("green", "version"))


    def test_cmd_env_nodef(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG is set, $HOME/.green does not
            exist
        Result: load --config
        """
        os.unlink(self.default_filename)
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename, HOME=self.tmpd):
            cfg = config.getConfig(self.cmd_filename)
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.cmd_filename,          cfg.get("green", "omit"))
            ae(self.cmd_run_coverage,      cfg.getboolean("green", "run-coverage"))
            ae(self.cmd_logging,           cfg.getboolean("green", "logging"))
            ae(self.env_html,              cfg.getboolean("green", "html"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "version")


    def test_cmd_noenv_def(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG unset, $HOME/.green exists
        Result: load --config
        """
        os.unlink(self.env_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.getConfig(self.cmd_filename)
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.cmd_filename,          cfg.get("green", "omit"))
            ae(self.cmd_run_coverage,      cfg.getboolean("green", "run-coverage"))
            ae(self.cmd_logging,           cfg.getboolean("green", "logging"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "html")
            ae(self.default_version,       cfg.getboolean("green", "version"))


    def test_cmd_noenv_nodef(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG unset, $HOME/.green does not exist
        Result: load --config
        """
        os.unlink(self.env_filename)
        os.unlink(self.default_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.getConfig(self.cmd_filename)
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.cmd_filename,          cfg.get("green", "omit"))
            ae(self.cmd_run_coverage,      cfg.getboolean("green", "run-coverage"))
            ae(self.cmd_logging,           cfg.getboolean("green", "logging"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "html")
            ar(configparser.NoOptionError, cfg.getboolean, "green", "version")


    def test_nocmd_env_def(self):
        """
        Setup: no --config option, $GREEN_CONFIG is set, $HOME/.green exists
        Result: load $GREEN_CONFIG
        """
        os.unlink(self.cmd_filename)
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename, HOME=self.tmpd):
            cfg = config.getConfig()
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.env_filename,          cfg.get("green", "omit"))
            ar(configparser.NoOptionError, cfg.get, "green", "run-coverage")
            ae(self.env_logging,           cfg.getboolean("green", "logging"))
            ae(self.env_html,              cfg.getboolean("green", "html"))
            ae(self.default_version,       cfg.getboolean("green", "version"))


    def test_nocmd_env_nodef(self):
        """
        Setup: no --config option, $GREEN_CONFIG is set, $HOME/.green does not
            exist
        Result: load $GREEN_CONFIG
        """
        os.unlink(self.cmd_filename)
        os.unlink(self.default_filename)
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename, HOME=self.tmpd):
            cfg = config.getConfig()
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.env_filename,          cfg.get("green", "omit"))
            ar(configparser.NoOptionError, cfg.get, "green", "run-coverage")
            ae(self.env_logging,           cfg.getboolean("green", "logging"))
            ae(self.env_html,              cfg.getboolean("green", "html"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "version")


    def test_nocmd_noenv_def(self):
        """
        Setup: no --config option, $GREEN_CONFIG unset, $HOME/.green exists
        Result: load $HOME/.green
        """
        os.unlink(self.cmd_filename)
        os.unlink(self.env_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.getConfig()
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],                  cfg.sections())
            ae(self.default_filename,      cfg.get("green", "omit"))
            ar(configparser.NoOptionError, cfg.get, "green", "run-coverage")
            ae(self.default_logging,       cfg.getboolean("green", "logging"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "html")
            ae(self.default_version,       cfg.getboolean("green", "version"))


    def test_nocmd_noenv_nodef(self):
        """
        Setup: no --config option, $GREEN_CONFIG unset, no $HOME/.green
        Result: empty config
        """
        os.unlink(self.default_filename)
        os.unlink(self.env_filename)
        os.unlink(self.cmd_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.getConfig()
            ae = self.assertEqual
            ar = self.assertRaises
            ae([], cfg.sections())
            ar(configparser.NoSectionError, cfg.get, "green", "omit")
            ar(configparser.NoSectionError, cfg.get, "green", "run-coverage")
            ar(configparser.NoSectionError, cfg.get, "green", "logging")
            ar(configparser.NoSectionError, cfg.get, "green", "html")
            ar(configparser.NoSectionError, cfg.get, "green", "version")



class TestMergeConfig(ConfigBase):
    """
    Merging config files and command-line arguments works as expected.
    """


    def test_overwrite(self):
        """
        Non-default command-line argument values overwrite config values.
        """
        # This config environment should set the values we look at to False and
        # a filename in omit
        s = StringIO()
        gs = GreenStream(s)
        saved_stdout = config.sys.stdout
        config.sys.stdout = gs
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename, HOME=self.tmpd):
            new_args = copy.deepcopy(config.default_args)

            new_args.omit         = 'omitstuff'
            new_args.run_coverage = True
            new_args.logging      = True
            new_args.html         = True
            new_args.version      = True

            new_args.config = self.cmd_filename
            computed_args = config.mergeConfig(new_args, config.default_args)

            self.assertEqual(computed_args.omit,         'omitstuff')
            self.assertEqual(computed_args.run_coverage, new_args.run_coverage)
            self.assertEqual(computed_args.logging,      new_args.logging)
            self.assertEqual(computed_args.html,         new_args.html)
            self.assertEqual(computed_args.version,      new_args.version)
        config.sys.stdout = saved_stdout


    def test_no_overwrite(self):
        """
        Default command-line arguments do not overwrite config values.
        """
        # This config environment should set logging to True
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename, HOME=""):
            # The default for logging in arguments is False
            da = config.default_args
            computed_args = config.mergeConfig(da, da)
            self.assertEqual(computed_args.logging, True)


    def test_targets(self):
        "The targets passed in make it through mergeConfig"
        "The specified target gets parsed"
        config.sys.argv = ['', 'target1', 'target2']
        args = config.parseArguments()
        args = config.mergeConfig(args)
        self.assertEqual(args.targets, ['target1', 'target2'])


    def test_forgotToUpdateMerge(self):
         """
         mergeConfig raises an exception for unknown cmdline args
         """
         new_args = copy.deepcopy(config.default_args)
         new_args.new_option = True

         self.assertRaises(NotImplementedError, config.mergeConfig, new_args,
                 config.default_args)
