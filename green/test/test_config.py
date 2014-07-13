import ConfigParser
import pdb
import os
import sys
import shutil
import tempfile
import unittest
from green import config

"""
Testcases:

    test_cmd_env_def
    Setup: --config on cmd, $GREEN_CONF is set, $HOME/.green exists
    Result: load --config

    test_cmd_env_nodef
    Setup: --config on cmd, $GREEN_CONF is set, $HOME/.green does not exist
    Result: load --config

    test_cmd_noenv_def
    Setup: --config on cmd, $GREEN_CONF unset, $HOME/.green exists
    Result: load --config

    test_cmd_noenv_nodef
    Setup: --config on cmd, $GREEN_CONF unset, $HOME/.green does not exist
    Result: load --config

    test_nocmd_env_def
    Setup: no --config option, $GREEN_CONF is set, $HOME/.green exists
    Result: load $GREEN_CONF

    test_nocmd_env_nodef
    Setup: no --config option, $GREEN_CONF is set, $HOME/.green does not exist
    Result: load $GREEN_CONF

    test_nocmd_noenv_def
    Setup: no --config option, $GREEN_CONF unset, $HOME/.green exists
    Result: load $HOME/.green

    test_nocmd_noenv_nodef
    Setup: no --config option, $GREEN_CONF unset, $HOME/.green does not exist
    Result: empty config

"""

def funcname():
    return sys._getframe(1).f_code.co_name

class env_excursion(object):
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
        

class TestConfig(unittest.TestCase):

    def setUp(self):
        if hasattr(config.get_config, "_cfg"):
            del config.get_config._cfg
        self.tmpd = tempfile.mkdtemp()
        self.defname = os.path.join(self.tmpd, ".green")
        self.write_file(self.defname,
                        ["# this is a test config file for green",
                         "[green]",
                         "foo = bar",
                         "filename = %s" % self.defname,
                         "[default_config]",
                         "something = to be here",
                         ])
        self.envname = os.path.join(self.tmpd, "green.env")
        self.write_file(self.envname,
                        ["# this is a test config file for green",
                         "[green]",
                         "different = not the same",
                         "filename = %s" % self.envname,
                         "[env_config]",
                         "this_section = ignored",
                         ])
        self.cmdname = os.path.join(self.tmpd, "green.cmd")
        self.write_file(self.cmdname,
                        ["# this is a test config file for green",
                         "[green]",
                         "cmdline = yes",
                         "filename = %s" % self.cmdname,
                         "[cmdline_config]",
                         "nothing = here",
                         ])

    def tearDown(self):
        shutil.rmtree(self.tmpd)

    def test_cmd_env_def(self):
        """
        Setup: --config on cmd, $GREEN_CONF is set, $HOME/.green exists
        Result: load --config
        """
        with env_excursion(GREEN_CONF=self.envname, HOME=self.tmpd):
            config.load_config(self.cmdname)
            cfg = config.get_config()
            self.assertEqual(["green", "cmdline_config"], cfg.sections())
            self.assertEqual("yes", cfg.get("green", "cmdline"))
            self.assertEqual(self.cmdname, cfg.get("green", "filename"))
            self.assertRaises(ConfigParser.NoOptionError,
                              cfg.get, "green", "different")
            self.assertRaises(ConfigParser.NoOptionError,
                              cfg.get, "green", "foo")
            self.assertRaises(ConfigParser.NoSectionError,
                              cfg.get, "env_config", "this_section")
            self.assertRaises(ConfigParser.NoSectionError,
                              cfg.get, "default_config", "something")

    def test_cmd_env_nodef(self):
        """
        Setup: --config on cmd, $GREEN_CONF is set, $HOME/.green does not exist
        Result: load --config
        """
        os.unlink(self.defname)
        with env_excursion(GREEN_CONF=self.envname, HOME=self.tmpd):
            config.load_config(self.cmdname)
            cfg = config.get_config()
            self.assertEqual(["green", "cmdline_config"], cfg.sections())
            self.assertEqual("yes", cfg.get("green", "cmdline"))
            self.assertEqual(self.cmdname, cfg.get("green", "filename"))
            self.assertRaises(ConfigParser.NoOptionError,
                              cfg.get, "green", "different")
            self.assertRaises(ConfigParser.NoOptionError,
                              cfg.get, "green", "foo")
            self.assertRaises(ConfigParser.NoSectionError,
                              cfg.get, "env_config", "this_section")
            self.assertRaises(ConfigParser.NoSectionError,
                              cfg.get, "default_config", "something")

    def test_cmd_noenv_def(self):
        """
        Setup: --config on cmd, $GREEN_CONF unset, $HOME/.green exists
        Result: load --config
        """
        os.unlink(self.envname)
        with env_excursion(GREEN_CONF=None, HOME=self.tmpd):
            config.load_config(self.cmdname)
            cfg = config.get_config()
            self.assertEqual(["green", "cmdline_config"], cfg.sections())
            self.assertEqual("yes", cfg.get("green", "cmdline"))
            self.assertEqual(self.cmdname, cfg.get("green", "filename"))
            self.assertRaises(ConfigParser.NoOptionError,
                              cfg.get, "green", "different")
            self.assertRaises(ConfigParser.NoOptionError,
                              cfg.get, "green", "foo")
            self.assertRaises(ConfigParser.NoSectionError,
                              cfg.get, "env_config", "this_section")
            self.assertRaises(ConfigParser.NoSectionError,
                              cfg.get, "default_config", "something")

    def test_cmd_noenv_nodef(self):
        """
        Setup: --config on cmd, $GREEN_CONF unset, $HOME/.green does not exist
        Result: load --config
        """
        os.unlink(self.envname)
        os.unlink(self.defname)
        with env_excursion(GREEN_CONF=None, HOME=self.tmpd):
            config.load_config(self.cmdname)
            cfg = config.get_config()
            self.assertEqual(["green", "cmdline_config"], cfg.sections())
            self.assertEqual("yes", cfg.get("green", "cmdline"))
            self.assertEqual(self.cmdname, cfg.get("green", "filename"))
            self.assertRaises(ConfigParser.NoOptionError,
                              cfg.get, "green", "different")
            self.assertRaises(ConfigParser.NoOptionError,
                              cfg.get, "green", "foo")
            self.assertRaises(ConfigParser.NoSectionError,
                              cfg.get, "env_config", "this_section")
            self.assertRaises(ConfigParser.NoSectionError,
                              cfg.get, "default_config", "something")

    def test_nocmd_env_def(self):
        """
        Setup: no --config option, $GREEN_CONF is set, $HOME/.green exists
        Result: load $GREEN_CONF
        """
        os.unlink(self.cmdname)
        with env_excursion(GREEN_CONF=self.envname, HOME=self.tmpd):
            cfg = config.get_config()
            self.assertEqual(["green", "env_config"], cfg.sections())
            self.assertEqual("not the same", cfg.get('green', 'different'))
            self.assertEqual(self.envname, cfg.get('green', 'filename'))
            self.assertRaises(ConfigParser.NoOptionError,
                              cfg.get, "green", "cmdline")
            self.assertRaises(ConfigParser.NoOptionError,
                              cfg.get, "green", "foo")
            self.assertRaises(ConfigParser.NoSectionError,
                              cfg.get, "cmdline_config", "this_section")
            self.assertRaises(ConfigParser.NoSectionError,
                              cfg.get, "default_config", "something")


    def test_nocmd_env_nodef(self):
        """
        Setup: no --config option, $GREEN_CONF is set, $HOME/.green does not exist
        Result: load $GREEN_CONF
        """
        os.unlink(self.cmdname)
        os.unlink(self.defname)
        with env_excursion(GREEN_CONF=self.envname, HOME=self.tmpd):
            cfg = config.get_config()
            self.assertEqual(["green", "env_config"], cfg.sections())
            self.assertEqual("not the same", cfg.get('green', 'different'))
            self.assertEqual(self.envname, cfg.get('green', 'filename'))
            self.assertRaises(ConfigParser.NoOptionError,
                              cfg.get, "green", "cmdline")
            self.assertRaises(ConfigParser.NoOptionError,
                              cfg.get, "green", "foo")
            self.assertRaises(ConfigParser.NoSectionError,
                              cfg.get, "cmdline_config", "this_section")
            self.assertRaises(ConfigParser.NoSectionError,
                              cfg.get, "default_config", "something")


    def test_nocmd_noenv_def(self):
        """
        Setup: no --config option, $GREEN_CONF unset, $HOME/.green exists
        Result: load $HOME/.green
        """
        os.unlink(self.cmdname)
        os.unlink(self.envname)
        with env_excursion(GREEN_CONF=None, HOME=self.tmpd):
            cfg = config.get_config()
            self.assertEqual(["green", "default_config"], cfg.sections())
            self.assertEqual("bar", cfg.get('green', 'foo'))
            self.assertEqual(self.defname, cfg.get('green', 'filename'))
            self.assertRaises(ConfigParser.NoOptionError,
                              cfg.get, "green", "cmdline")
            self.assertRaises(ConfigParser.NoOptionError,
                              cfg.get, "green", "different")
            self.assertRaises(ConfigParser.NoSectionError,
                              cfg.get, "cmdline_config", "this_section")
            self.assertRaises(ConfigParser.NoSectionError,
                              cfg.get, "env_config", "something")

    def test_nocmd_noenv_nodef(self):
        """
        Setup: no --config option, $GREEN_CONF unset, no $HOME/.green
        Result: empty config
        """
        os.unlink(self.defname)
        os.unlink(self.envname)
        os.unlink(self.cmdname)
        with env_excursion(GREEN_CONF=None, HOME=self.tmpd):
            cfg = config.get_config()
            self.assertEqual([], cfg.sections())
        
    def write_file(self, path, lines):
        f = open(path, 'w')
        f.writelines([x + "\n" for x in lines])
        f.close()
