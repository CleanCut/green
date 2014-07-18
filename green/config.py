from __future__ import unicode_literals # pragma: no cover
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
try:              # pragma: no cover
    import configparser
except:           # pragma: no cover
    import ConfigParser as configparser

import copy       # pragma: no cover
import os         # pragma: no cover

# Used for debugging output in cmdline, since we can't do debug output here.
files_loaded = [] # pragma: no cover



class ConfigFile(object): # pragma: no cover
    """
    Filehandle wrapper that adds a "[green]" section to the start of a config
    file so that users don't actually have to manually add a [green] section.

    Works with configparser versions from both Python 2 and 3
    """


    def __init__(self, filepath):
        self.first = True
        self.lines = open(filepath).readlines()


    # Python 2
    def readline(self):
        try:
            return self.__next__()
        except StopIteration:
            return ''


    # Python 3
    def __iter__(self):
        return self


    def __next__(self):
        if self.first:
            self.first = False
            return "[green]\n"
        if self.lines:
            return self.lines.pop(0)
        raise StopIteration



# Since this must be imported before coverage is started, we get erroneous
# reports of not covering this function during our internal coverage tests.
def get_config(filepath=None): # pragma: no cover
    """
    Get the Green config file settings.

    All available config files are read.  If settings are in multiple configs,
    the last value encountered wins.  Values specified on the command-line take
    precedence over all config file settings.

    Returns: A ConfigParser object.
    """
    parser = configparser.ConfigParser()

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
        global files_loaded
        files_loaded = filepaths
        # Python 3 has parser.read_file(iterator) while Python2 has
        # parser.readfp(obj_with_readline)
        read_func = getattr(parser, 'read_file', getattr(parser, 'readfp'))
        for filepath in filepaths:
            read_func(ConfigFile(filepath))

    return parser


# Since this must be imported before coverage is started, we get erroneous
# reports of not covering this function during our internal coverage tests.
def merge_config(args, default_args): # pragma: no cover
    """
    I take in a namespace created by the ArgumentParser in cmdline.main() and
    merge in options from configuration files.  The config items only replace
    argument items that are set to default value.

    Returns: I return a new argparse.Namespace
    """
    config = get_config(args.config)
    new_args = copy.deepcopy(default_args) # Default by default!

    for name, args_value in dict(args._get_kwargs()).items():
        # Config options overwrite default options
        config_getter = None
        if name in ['html', 'termcolor', 'notermcolor', 'help', 'logging',
                'version', 'run_coverage']:
            config_getter = config.getboolean
        elif name in ['subprocesses', 'debug', 'verbose']:
            config_getter = config.getint
        elif name in ['omit']:
            config_getter = config.get
        elif name in ['targets', 'help', 'config']:
            pass # Some options only make sense coming on the command-line.
        else:
            raise NotImplementedError(name)

        if config_getter:
            try:
                config_value = config_getter('green', name.replace('_','-'))
                setattr(new_args, name, config_value)
            except (configparser.NoSectionError, configparser.NoOptionError):
                pass

        # Command-line values overwrite defaults and config values
        if args_value != getattr(default_args, name):
            setattr(new_args, name, args_value)

    return new_args
