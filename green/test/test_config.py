from __future__ import annotations

import configparser
import copy
import pathlib
from io import StringIO
import os
import shutil
import tempfile
import unittest
from typing import Sequence

from green import config
from green.output import GreenStream


class ParseArguments(unittest.TestCase):
    def test_target(self):
        """
        The specified target gets parsed
        """
        config.sys.argv = ["", "target1", "target2"]
        args = config.parseArguments()
        self.assertEqual(args.targets, ["target1", "target2"])

    def test_absent(self):
        """
        Arguments not specified on the command-line are not present in the args
        object.
        """
        config.sys.argv = ["", "--debug"]
        args = config.parseArguments()
        self.assertEqual(getattr(args, "debug", "not there"), True)
        self.assertEqual(getattr(args, "verbose", "not there"), "not there")
        self.assertEqual(getattr(args, "targets", "not there"), "not there")
        self.assertEqual(getattr(args, "file_pattern", "not there"), "not there")


class ModifiedEnvironment:
    """
    I am a context manager that sets up environment variables for a test case.
    """

    def __init__(self, **kwargs: str | None) -> None:
        self.prev = {}
        self.excur = kwargs
        for k in kwargs:
            self.prev[k] = os.getenv(k)

    def __enter__(self) -> None:
        self.update_environment(self.excur)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.update_environment(self.prev)

    def update_environment(self, env: dict[str, str | None]) -> None:
        for key, value in env.items():
            if value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = value


class ConfigBase(unittest.TestCase):
    """
    I am an abstract base class that creates and destroys configuration files
    in a temporary directory with known values attached to self.
    """

    def _write_file(self, path: pathlib.Path, lines: Sequence[str]) -> None:
        path.write_text("\n".join(lines) + "\n")

    def setUp(self):
        self.tmpd = tmpd = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmpd)
        # Set CWD to known empty directory so we don't pick up some other .green
        # file from the CWD tests are actually run from.
        self.addCleanup(os.chdir, pathlib.Path.cwd())
        cwd_dir = tmpd / "cwd"
        cwd_dir.mkdir(exist_ok=True, parents=True)
        os.chdir(cwd_dir)
        # This represents the $HOME config file, and doubles for the current
        # working directory config file if we set CWD to self.tmpd
        self.default_filename = tmpd / ".green"
        self.default_logging = False
        self.default_version = False
        self.default_failfast = True
        self.default_termcolor = True
        self._write_file(
            self.default_filename,
            [
                "# this is a test config file for green",
                f"logging = {self.default_logging}",
                f"version = {self.default_version}",
                f"omit-patterns = {self.default_filename}",
                f"failfast = {self.default_failfast}",
                f"termcolor = {self.default_termcolor}",
            ],
        )
        self.env_filename = tmpd / "green.env"
        self.env_logging = True
        self.env_no_skip_report = False
        self._write_file(
            self.env_filename,
            [
                "# this is a test config file for green",
                f"logging = {self.env_logging}",
                f"omit-patterns = {self.env_filename}",
                f"no-skip-report = {self.env_no_skip_report}",
            ],
        )
        self.cmd_filename = self.tmpd / "green.cmd"
        self.cmd_logging = False
        self.cmd_run_coverage = False
        self._write_file(
            self.cmd_filename,
            [
                "# this is a test config file for green",
                f"logging = {self.cmd_logging}",
                f"omit-patterns = {self.cmd_filename}",
                f"run-coverage = {self.cmd_run_coverage}",
            ],
        )
        self.setup_filename = cwd_dir / "setup.cfg"
        self.setup_failfast = False
        self.setup_verbose = 3
        self._write_file(
            self.setup_filename,
            [
                "[green]",
                f"failfast = {self.setup_failfast}",
                f"verbose = {self.setup_verbose}",
            ],
        )


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
        self.default_filename.unlink(missing_ok=True)
        self.setup_filename.unlink(missing_ok=True)
        with ModifiedEnvironment(
            GREEN_CONFIG=str(self.env_filename), HOME=str(self.tmpd)
        ):
            cfg = config.getConfig(self.cmd_filename)
            self.assertEqual(["green"], cfg.sections())
            self.assertEqual(str(self.cmd_filename), cfg.get("green", "omit-patterns"))
            self.assertEqual(
                self.cmd_run_coverage, cfg.getboolean("green", "run-coverage")
            )
            self.assertEqual(self.cmd_logging, cfg.getboolean("green", "logging"))
            self.assertEqual(
                self.env_no_skip_report, cfg.getboolean("green", "no-skip-report")
            )
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "version"
            )
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "verbose"
            )

    def test_cmd_noenv_def_nosetup(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG unset, $HOME/.green exists,
            setup.cfg does not exist
        Result: load --config
        """
        os.unlink(self.env_filename)
        os.remove(self.setup_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=str(self.tmpd)):
            cfg = config.getConfig(self.cmd_filename)
            self.assertEqual(["green"], cfg.sections())
            self.assertEqual(str(self.cmd_filename), cfg.get("green", "omit-patterns"))
            self.assertEqual(
                self.cmd_run_coverage, cfg.getboolean("green", "run-coverage")
            )
            self.assertEqual(self.cmd_logging, cfg.getboolean("green", "logging"))
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "no-skip-report"
            )
            self.assertEqual(self.default_version, cfg.getboolean("green", "version"))
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "verbose"
            )

    def test_cmd_noenv_nodef_nosetup(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG unset, $HOME/.green does not
            exist, setup.cfg does not exist
        Result: load --config
        """
        os.unlink(self.env_filename)
        os.unlink(self.default_filename)
        os.remove(self.setup_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=str(self.tmpd)):
            cfg = config.getConfig(self.cmd_filename)
            self.assertEqual(["green"], cfg.sections())
            self.assertEqual(str(self.cmd_filename), cfg.get("green", "omit-patterns"))
            self.assertEqual(
                self.cmd_run_coverage, cfg.getboolean("green", "run-coverage")
            )
            self.assertEqual(self.cmd_logging, cfg.getboolean("green", "logging"))
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "no-skip-report"
            )
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "version"
            )
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "verbose"
            )

    def test_nocmd_env_cwd(self):
        """
        Setup: no --config option, $GREEN_CONFIG is set, .green in local dir,
        Result: load $GREEN_CONFIG
        """
        os.chdir(self.tmpd)  # setUp is already set to restore us to our pre-testing cwd
        os.unlink(self.cmd_filename)
        os.remove(self.setup_filename)
        with ModifiedEnvironment(
            GREEN_CONFIG=str(self.env_filename), HOME=str(self.tmpd)
        ):
            cfg = config.getConfig()
            self.assertEqual(["green"], cfg.sections())
            self.assertEqual(
                str(self.default_filename), cfg.get("green", "omit-patterns")
            )
            self.assertRaises(
                configparser.NoOptionError, cfg.get, "green", "run-coverage"
            )
            self.assertEqual(self.default_logging, cfg.getboolean("green", "logging"))
            self.assertEqual(
                self.env_no_skip_report, cfg.getboolean("green", "no-skip-report")
            )
            self.assertEqual(self.default_version, cfg.getboolean("green", "version"))
            self.assertRaises(
                configparser.NoOptionError, cfg.getint, "green", "verbose"
            )

    def test_nocmd_env_def_nosetup(self):
        """
        Setup: no --config option, $GREEN_CONFIG is set, $HOME/.green exists,
            setup.cfg does not exist
        Result: load $GREEN_CONFIG
        """
        self.cmd_filename.unlink(missing_ok=True)
        self.setup_filename.unlink(missing_ok=True)
        with ModifiedEnvironment(
            GREEN_CONFIG=str(self.env_filename), HOME=str(self.tmpd)
        ):
            cfg = config.getConfig()
            self.assertEqual(["green"], cfg.sections())
            self.assertEqual(str(self.env_filename), cfg.get("green", "omit-patterns"))
            self.assertRaises(
                configparser.NoOptionError, cfg.get, "green", "run-coverage"
            )
            self.assertEqual(self.env_logging, cfg.getboolean("green", "logging"))
            self.assertEqual(
                self.env_no_skip_report, cfg.getboolean("green", "no-skip-report")
            )
            self.assertEqual(self.default_version, cfg.getboolean("green", "version"))
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "verbose"
            )

    def test_nocmd_env_nodef_nosetup(self):
        """
        Setup: no --config option, $GREEN_CONFIG is set, $HOME/.green does not
            exist, setup.cfg does not exist
        Result: load $GREEN_CONFIG
        """
        self.cmd_filename.unlink(missing_ok=True)
        self.default_filename.unlink(missing_ok=True)
        self.setup_filename.unlink(missing_ok=True)
        with ModifiedEnvironment(
            GREEN_CONFIG=str(self.env_filename), HOME=str(self.tmpd)
        ):
            cfg = config.getConfig()
            self.assertEqual(["green"], cfg.sections())
            self.assertEqual(str(self.env_filename), cfg.get("green", "omit-patterns"))
            self.assertRaises(
                configparser.NoOptionError, cfg.get, "green", "run-coverage"
            )
            self.assertEqual(self.env_logging, cfg.getboolean("green", "logging"))
            self.assertEqual(
                self.env_no_skip_report, cfg.getboolean("green", "no-skip-report")
            )
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "version"
            )
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "verbose"
            )

    def test_nocmd_noenv_def_nosetup(self):
        """
        Setup: no --config option, $GREEN_CONFIG unset, $HOME/.green exists,
            setup.cfg does not exist
        Result: load $HOME/.green
        """
        os.unlink(self.cmd_filename)
        os.unlink(self.env_filename)
        os.remove(self.setup_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=str(self.tmpd)):
            cfg = config.getConfig()
            self.assertEqual(["green"], cfg.sections())
            self.assertEqual(
                str(self.default_filename), cfg.get("green", "omit-patterns")
            )
            self.assertRaises(
                configparser.NoOptionError, cfg.get, "green", "run-coverage"
            )
            self.assertEqual(self.default_logging, cfg.getboolean("green", "logging"))
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "no-skip-report"
            )
            self.assertEqual(self.default_version, cfg.getboolean("green", "version"))
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "verbose"
            )

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
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=str(self.tmpd)):
            cfg = config.getConfig()
            self.assertEqual([], cfg.sections())
            self.assertRaises(
                configparser.NoSectionError, cfg.get, "green", "omit-patterns"
            )
            self.assertRaises(
                configparser.NoSectionError, cfg.get, "green", "run-coverage"
            )
            self.assertRaises(configparser.NoSectionError, cfg.get, "green", "logging")
            self.assertRaises(
                configparser.NoSectionError, cfg.get, "green", "no-skip-report"
            )
            self.assertRaises(configparser.NoSectionError, cfg.get, "green", "version")
            self.assertRaises(configparser.NoSectionError, cfg.get, "green", "verbose")

    def test_cmd_env_nodef_setup(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG is set, $HOME/.green does not
            exist, setup.cfg exists
        Result: load --config
        """
        os.unlink(self.default_filename)
        with ModifiedEnvironment(
            GREEN_CONFIG=str(self.env_filename), HOME=str(self.tmpd)
        ):
            cfg = config.getConfig(self.cmd_filename)
            self.assertEqual(["green"], cfg.sections())
            self.assertEqual(str(self.cmd_filename), cfg.get("green", "omit-patterns"))
            self.assertEqual(
                self.cmd_run_coverage, cfg.getboolean("green", "run-coverage")
            )
            self.assertEqual(self.cmd_logging, cfg.getboolean("green", "logging"))
            self.assertEqual(
                self.env_no_skip_report, cfg.getboolean("green", "no-skip-report")
            )
            self.assertEqual(self.setup_verbose, cfg.getint("green", "verbose"))
            self.assertEqual(self.setup_failfast, cfg.getboolean("green", "failfast"))
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "version"
            )

    def test_cmd_noenv_def_setup(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG unset, $HOME/.green exists,
            setup.cfg exists
        Result: load --config
        """
        os.unlink(self.env_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=str(self.tmpd)):
            cfg = config.getConfig(self.cmd_filename)
            self.assertEqual(["green"], cfg.sections())
            self.assertEqual(str(self.cmd_filename), cfg.get("green", "omit-patterns"))
            self.assertEqual(
                self.cmd_run_coverage, cfg.getboolean("green", "run-coverage")
            )
            self.assertEqual(self.cmd_logging, cfg.getboolean("green", "logging"))
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "no-skip-report"
            )
            self.assertEqual(self.default_version, cfg.getboolean("green", "version"))
            self.assertEqual(self.setup_verbose, cfg.getint("green", "verbose"))
            self.assertEqual(self.setup_failfast, cfg.getboolean("green", "failfast"))

    def test_cmd_noenv_nodef_setup(self):
        """
        Setup: --config on cmd, $GREEN_CONFIG unset, $HOME/.green does not exist,
            setup.cfg exists
        Result: load --config
        """
        os.unlink(self.env_filename)
        os.unlink(self.default_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=str(self.tmpd)):
            cfg = config.getConfig(self.cmd_filename)
            self.assertEqual(["green"], cfg.sections())
            self.assertEqual(str(self.cmd_filename), cfg.get("green", "omit-patterns"))
            self.assertEqual(
                self.cmd_run_coverage, cfg.getboolean("green", "run-coverage")
            )
            self.assertEqual(self.cmd_logging, cfg.getboolean("green", "logging"))
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "no-skip-report"
            )
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "version"
            )
            self.assertEqual(self.setup_verbose, cfg.getint("green", "verbose"))
            self.assertEqual(self.setup_failfast, cfg.getboolean("green", "failfast"))

    def test_nocmd_env_def_setup(self):
        """
        Setup: no --config option, $GREEN_CONFIG is set, $HOME/.green exists,
            setup.cfg exists
        Result: load $GREEN_CONFIG
        """
        os.unlink(self.cmd_filename)
        with ModifiedEnvironment(
            GREEN_CONFIG=str(self.env_filename), HOME=str(self.tmpd)
        ):
            cfg = config.getConfig()
            self.assertEqual(["green"], cfg.sections())
            self.assertEqual(str(self.env_filename), cfg.get("green", "omit-patterns"))
            self.assertRaises(
                configparser.NoOptionError, cfg.get, "green", "run-coverage"
            )
            self.assertEqual(self.env_logging, cfg.getboolean("green", "logging"))
            self.assertEqual(
                self.env_no_skip_report, cfg.getboolean("green", "no-skip-report")
            )
            self.assertEqual(self.default_version, cfg.getboolean("green", "version"))
            self.assertEqual(self.setup_verbose, cfg.getint("green", "verbose"))
            self.assertEqual(self.setup_failfast, cfg.getboolean("green", "failfast"))

    def test_nocmd_env_nodef_setup(self):
        """
        Setup: no --config option, $GREEN_CONFIG is set, $HOME/.green does not
            exist, setup.cfg exists
        Result: load $GREEN_CONFIG
        """
        os.unlink(self.cmd_filename)
        os.unlink(self.default_filename)
        with ModifiedEnvironment(
            GREEN_CONFIG=str(self.env_filename), HOME=str(self.tmpd)
        ):
            cfg = config.getConfig()
            self.assertEqual(["green"], cfg.sections())
            self.assertEqual(str(self.env_filename), cfg.get("green", "omit-patterns"))
            self.assertRaises(
                configparser.NoOptionError, cfg.get, "green", "run-coverage"
            )
            self.assertEqual(self.env_logging, cfg.getboolean("green", "logging"))
            self.assertEqual(
                self.env_no_skip_report, cfg.getboolean("green", "no-skip-report")
            )
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "version"
            )
            self.assertEqual(self.setup_verbose, cfg.getint("green", "verbose"))
            self.assertEqual(self.setup_failfast, cfg.getboolean("green", "failfast"))

    def test_nocmd_noenv_def_setup(self):
        """
        Setup: no --config option, $GREEN_CONFIG unset, $HOME/.green exists,
            setup.cfg exists
        Result: load $HOME/.green
        """
        os.unlink(self.cmd_filename)
        os.unlink(self.env_filename)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=str(self.tmpd)):
            cfg = config.getConfig()
            self.assertEqual(["green"], cfg.sections())
            self.assertEqual(
                str(self.default_filename), cfg.get("green", "omit-patterns")
            )
            self.assertRaises(
                configparser.NoOptionError, cfg.get, "green", "run-coverage"
            )
            self.assertEqual(self.default_logging, cfg.getboolean("green", "logging"))
            self.assertRaises(
                configparser.NoOptionError, cfg.getboolean, "green", "no-skip-report"
            )
            self.assertEqual(self.default_version, cfg.getboolean("green", "version"))
            self.assertEqual(self.setup_verbose, cfg.getint("green", "verbose"))
            self.assertEqual(self.setup_failfast, cfg.getboolean("green", "failfast"))

    def test_nocmd_noenv_nodef_setup(self):
        """
        Setup: no --config option, $GREEN_CONFIG unset, no $HOME/.green,
            setup.cfg exists
        Result: empty config
        """
        self.default_filename.unlink(missing_ok=True)
        self.env_filename.unlink(missing_ok=True)
        self.cmd_filename.unlink(missing_ok=True)
        with ModifiedEnvironment(GREEN_CONFIG=None, HOME=str(self.tmpd)):
            cfg = config.getConfig()
            self.assertEqual(self.setup_verbose, cfg.getint("green", "verbose"))
            self.assertEqual(self.setup_failfast, cfg.getboolean("green", "failfast"))
            self.assertRaises(
                configparser.NoOptionError, cfg.get, "green", "omit-patterns"
            )
            self.assertRaises(
                configparser.NoOptionError, cfg.get, "green", "run-coverage"
            )
            self.assertRaises(configparser.NoOptionError, cfg.get, "green", "logging")
            self.assertRaises(
                configparser.NoOptionError, cfg.get, "green", "no-skip-report"
            )
            self.assertRaises(configparser.NoOptionError, cfg.get, "green", "version")


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
        self.addCleanup(setattr, config.sys, "stdout", saved_stdout)
        with ModifiedEnvironment(
            GREEN_CONFIG=str(self.env_filename), HOME=str(self.tmpd)
        ):
            new_args = copy.deepcopy(config.get_default_args())

            new_args.omit_patterns = "omitstuff"
            new_args.run_coverage = True
            new_args.logging = True
            new_args.no_skip_report = True
            new_args.version = True

            new_args.config = self.cmd_filename
            computed_args = config.mergeConfig(new_args, testing=True)

            self.assertEqual(computed_args.omit_patterns, "omitstuff")
            self.assertEqual(computed_args.run_coverage, new_args.run_coverage)
            self.assertEqual(computed_args.logging, new_args.logging)
            self.assertEqual(computed_args.no_skip_report, new_args.no_skip_report)
            self.assertEqual(computed_args.version, new_args.version)

    def test_no_overwrite(self):
        """
        Default unspecified command-line args do not overwrite config values.
        """
        # This config environment should set logging to True
        with ModifiedEnvironment(GREEN_CONFIG=str(self.env_filename), HOME=""):
            # The default for logging in arguments is False
            da = copy.deepcopy(config.get_default_args())
            del da.logging
            computed_args = config.mergeConfig(da, testing=True)
            self.assertEqual(computed_args.logging, True)

    def test_specified_command_line(self):
        """
        Specified command-line arguments always overwrite config file values
        """
        with ModifiedEnvironment(HOME=str(self.tmpd)):
            new_args = copy.deepcopy(config.get_default_args())
            new_args.failfast = True  # same as config, for sanity
            new_args.logging = True  # different than config, not default
            del new_args.version  # Not in arguments, should get config value
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
        config.sys.argv = ["", "target1", "target2"]
        args = config.parseArguments()
        args = config.mergeConfig(args)
        self.assertEqual(args.targets, ["target1", "target2"])

    def test_forgot_to_update_merge(self):
        """
        mergeConfig raises an exception for unknown cmdline args
        """
        default_args = config.get_default_args()
        orig_args = copy.deepcopy(default_args)
        self.addCleanup(setattr, config, "default_args", orig_args)

        default_args.new_option = True
        new_args = copy.deepcopy(default_args)

        try:
            with self.assertRaises(NotImplementedError):
                config.mergeConfig(new_args, testing=True)
        finally:
            config.get_default_args.cache_clear()
