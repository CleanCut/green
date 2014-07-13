from __future__ import unicode_literals
"""
Configuration settings are read in this order:

1) ~/.green
2) A config file specified by the environment variable $GREEN_CONFIG
3) A config file specified by the command-line argument --config FILE
4) Command-line arguments.

Any arguments specified in more than one place will be overwritten by the value
of the last place the setting is seen.  So, for example, if a setting is turned
on in ~/.green and turned off by a command-line argument, then the setting will
be turned off.
"""
try:
    import configparser as cp
except: # pragma: no cover
    import ConfigParser as cp
import logging
import os


def get_config(filepath=None):
    """
    Get the Green config file settings.

    All available config files are read.  If settings are in multiple configs,
    the last value encountered wins.  Values specified on the command-line take
    precedence over all config file settings.

    Returns: A ConfigParser object.
    """
    config_parser = cp.ConfigParser()

    filepaths = []
    # Lowest priority goes first in the list
    home = os.getenv("HOME")
    if home:
        default_filepath = os.path.join(home, ".green")
        if os.path.isfile(default_filepath):
            filepaths.append(default_filepath)

    # Medium priority
    env_filepath = os.getenv("GREEN_CONFIG")
    if env_filepath and os.path.isfile(env_filepath):
        filepaths.append(env_filepath)

    # Highest priority
    if filepath and os.path.isfile(filepath):
        filepaths.append(filepath)

    if filepaths:
        logging.debug("Loading config options from: " + ", ".join(filepaths))
        config_parser.read(filepaths)

    return config_parser
