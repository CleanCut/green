try:
    import configparser
except:
    import ConfigParser as configparser
import os
import shutil
import tempfile
import unittest

from green import config
from green import cmdline



class ModifiedEnvironment(object):


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


    def _write_file(self, path, lines):
        f = open(path, 'w')
        f.writelines([x + "\n" for x in lines])
        f.close()


    def setUp(self):
        self.tmpd = tempfile.mkdtemp()
        self.default_filename = os.path.join(self.tmpd, ".green")
        self.default_logging = False
        self.default_version = True
        self._write_file(self.default_filename,
                        ["# this is a test config file for green",
                         "[green]",
                         "logging = {}".format(str(self.default_logging)),
                         "version = {}".format(str(self.default_version)),
                         "omit = {}".format(self.default_filename),
                         ])
        self.env_filename = os.path.join(self.tmpd, "green.env")
        self.env_logging = True
        self.env_html = True
        self._write_file(self.env_filename,
                        ["# this is a test config file for green",
                         "[green]",
                         "logging = {}".format(str(self.env_logging)),
                         "omit = {}".format(self.env_filename),
                         "html = {}".format(self.env_html),
                         ])
        self.cmd_filename = os.path.join(self.tmpd, "green.cmd")
        self.cmd_logging = True
        self.cmd_run_coverage = True
        self._write_file(self.cmd_filename,
                        ["# this is a test config file for green",
                         "[green]",
                         "logging = {}".format(str(self.cmd_logging)),
                         "omit = {}".format(self.cmd_filename),
                         "run-coverage = {}".format(self.cmd_run_coverage),
                         ])


    def tearDown(self):
        shutil.rmtree(self.tmpd)



class TestMergeConfig(ConfigBase):


    def test_something(self):
        pass



class TestConfig(ConfigBase):


    def test_cmd_env_def(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG is set, $HOME/.green exists
        Result: load --config
        """
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename, HOME=self.tmpd):
            cfg = config.get_config(self.cmd_filename)
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
            cfg = config.get_config(self.cmd_filename)
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],             cfg.sections())
            ae(self.cmd_filename,     cfg.get("green", "omit"))
            ae(self.cmd_run_coverage, cfg.getboolean("green", "run-coverage"))
            ae(self.cmd_logging,      cfg.getboolean("green", "logging"))
            ae(self.env_html,         cfg.getboolean("green", "html"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "version")


    def test_cmd_noenv_def(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG unset, $HOME/.green exists
        Result: load --config
        """
        os.unlink(self.env_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.get_config(self.cmd_filename)
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],             cfg.sections())
            ae(self.cmd_filename,     cfg.get("green", "omit"))
            ae(self.cmd_run_coverage, cfg.getboolean("green", "run-coverage"))
            ae(self.cmd_logging,      cfg.getboolean("green", "logging"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "html")
            ae(self.default_version,  cfg.getboolean("green", "version"))


    def test_cmd_noenv_nodef(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG unset, $HOME/.green does not exist
        Result: load --config
        """
        os.unlink(self.env_filename)
        os.unlink(self.default_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.get_config(self.cmd_filename)
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],             cfg.sections())
            ae(self.cmd_filename,     cfg.get("green", "omit"))
            ae(self.cmd_run_coverage, cfg.getboolean("green", "run-coverage"))
            ae(self.cmd_logging,      cfg.getboolean("green", "logging"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "html")
            ar(configparser.NoOptionError, cfg.getboolean, "green", "version")


    def test_nocmd_env_def(self):
        """
        Setup: no --config option, $GREEN_CONFIG is set, $HOME/.green exists
        Result: load $GREEN_CONFIG
        """
        os.unlink(self.cmd_filename)
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename, HOME=self.tmpd):
            cfg = config.get_config()
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],             cfg.sections())
            ae(self.env_filename,     cfg.get("green", "omit"))
            ar(configparser.NoOptionError, cfg.get, "green", "run-coverage")
            ae(self.env_logging,      cfg.getboolean("green", "logging"))
            ae(self.env_html,         cfg.getboolean("green", "html"))
            ae(self.default_version,  cfg.getboolean("green", "version"))


    def test_nocmd_env_nodef(self):
        """
        Setup: no --config option, $GREEN_CONFIG is set, $HOME/.green does not
            exist
        Result: load $GREEN_CONFIG
        """
        os.unlink(self.cmd_filename)
        os.unlink(self.default_filename)
        with ModifiedEnvironment(GREEN_CONFIG=self.env_filename, HOME=self.tmpd):
            cfg = config.get_config()
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],             cfg.sections())
            ae(self.env_filename,     cfg.get("green", "omit"))
            ar(configparser.NoOptionError, cfg.get, "green", "run-coverage")
            ae(self.env_logging,      cfg.getboolean("green", "logging"))
            ae(self.env_html,         cfg.getboolean("green", "html"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "version")


    def test_nocmd_noenv_def(self):
        """
        Setup: no --config option, $GREEN_CONFIG unset, $HOME/.green exists
        Result: load $HOME/.green
        """
        os.unlink(self.cmd_filename)
        os.unlink(self.env_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.get_config()
            ae = self.assertEqual
            ar = self.assertRaises
            ae(["green"],             cfg.sections())
            ae(self.default_filename,     cfg.get("green", "omit"))
            ar(configparser.NoOptionError, cfg.get, "green", "run-coverage")
            ae(self.default_logging,      cfg.getboolean("green", "logging"))
            ar(configparser.NoOptionError, cfg.getboolean, "green", "html")
            ae(self.default_version,  cfg.getboolean("green", "version"))


    def test_nocmd_noenv_nodef(self):
        """
        Setup: no --config option, $GREEN_CONFIG unset, no $HOME/.green
        Result: empty config
        """
        os.unlink(self.default_filename)
        os.unlink(self.env_filename)
        os.unlink(self.cmd_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=self.tmpd):
            cfg = config.get_config()
            ae = self.assertEqual
            ar = self.assertRaises
            ae([], cfg.sections())
            ar(configparser.NoSectionError, cfg.get, "green", "omit")
            ar(configparser.NoSectionError, cfg.get, "green", "run-coverage")
            ar(configparser.NoSectionError, cfg.get, "green", "logging")
            ar(configparser.NoSectionError, cfg.get, "green", "html")
            ar(configparser.NoSectionError, cfg.get, "green", "version")
