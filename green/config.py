from __future__ import unicode_literals # pragma: no cover
from __future__ import print_function   # pragma: no cover
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

We have to use this entire file before we can turn coverage on, so we exclude
it from coverage.  We still have tests, though!
"""

import argparse             # pragma: no cover
try:                        # pragma: no cover
    import configparser
except:                     # pragma: no cover
    import ConfigParser as configparser
try:                        # pragma: no cover
    import coverage
    coverage_version = "Coverage {}".format(coverage.__version__)
except:                     # pragma: no cover
    coverage = None
    coverage_version = "Coverage Not Installed"

import copy                 # pragma: no cover
import logging              # pragma: no cover
import os                   # pragma: no cover
import sys                  # pragma: no cover
import tempfile             # pragma: no cover
from textwrap import dedent # pragma: no cover
import multiprocessing      # pragma: no cover

# Used for debugging output in cmdline, since we can't do debug output here.
files_loaded = [] # pragma: no cover

# Set the defaults in a re-usable way
default_args             = argparse.Namespace( # pragma: no cover
        targets          = ['.'], # Not in configs
        processes        = multiprocessing.cpu_count(),
        initializer      = '',
        finalizer        = '',
        termcolor        = None,
        notermcolor      = None,
        disable_windows  = False,
        allow_stdout     = False,
        quiet_stdout     = False,
        no_skip_report   = False,
        help             = False, # Not in configs
        version          = False,
        logging          = False,
        debug            = 0,
        verbose          = 1,
        failfast         = False,
        config           = None,  # Not in configs
        file_pattern     = 'test*.py',
        test_pattern     = '*',
        run_coverage     = False,
        clear_omit       = False,
        omit_patterns    = None,
        include_patterns = None,
        completion_file  = False,
        completions      = False,
        options          = False,
        # These are not really options, they are added later for convenience
        parser           = None,
        store_opt        = None,
        # not implemented, but unittest stub in place
        warnings         = '',
        )


class StoreOpt(): # pragma: no cover
    """
    Helper class for storing lists of the options themselves to hand out to the
    shell completion scripts.
    """


    def __init__(self):
        self.options = []
        self.options = []


    def __call__(self, action):
        self.options.extend(action.option_strings[0:2])




def parseArguments(): # pragma: no cover
    """
    I parse arguments in sys.argv and return the args object.  The parser
    itself is available as args.parser.

    Adds the following members to args:
        parser    = the parser object
        store_opt = the StoreOpt object
    """
    store_opt = StoreOpt()
    parser = argparse.ArgumentParser(
            prog='green',
            usage='%(prog)s [options] [target [target2 ...]]',
            add_help=False,
            description=dedent(
                """
                Green is a clean, colorful test runner for Python unit tests.
                """.rstrip()),
            epilog=dedent(
                """
                ENABLING SHELL COMPLETION

                  To enable bash- or zsh-completion, add the line below to the end of your
                  .bashrc or .zshrc file (or equivalent config file):

                    which green >& /dev/null && source "$( green --completion-file )"

                  Warning!  Generating a completion list actually discovers and loads tests
                  -- this can be very slow if you run it in huge directories!

                CONFIG FILES

                  Green will look for and process three config files if found:
                  1) $HOME/.green
                  2) $GREEN_CONFIG
                  3) A file specified with "--config FILE"

                  Config file format is simply "option = value" on separate lines.  "option" is
                  the same as the long options above, just without the "--".

                  Most values should be "True" or "False".  Accumulated values (verbose, debug)
                  should be specified as integers ("-vv" would be "verbose = 2").

                  Example:

                    verbose       = 2
                    logging       = True
                    omit-patterns = myproj*,*prototype*
                """.rstrip()),
            formatter_class=argparse.RawDescriptionHelpFormatter)

    target_args = parser.add_argument_group("Target Specification")
    target_args.add_argument('targets', action='store', nargs='*',
        metavar='target',
        help=("""Targets to test.  Any number of targets may be specified.  If
        blank, then discover all testcases in the current directory tree.  Can
        be a directory (or package), file (or module), or fully-qualified
        'dotted name' like proj.tests.test_things.TestStuff.  If a directory
        (or package) is specified, then we will attempt to discover all tests
        under the directory (even if the directory is a package and the tests
        would not be accessible through the package's scope).  In all other
        cases, only tests accessible from introspection of the object will
        be loaded."""),
        default=argparse.SUPPRESS)

    concurrency_args = parser.add_argument_group("Concurrency Options")
    store_opt(
        concurrency_args.add_argument('-s', '--processes', action='store',
            type=int, metavar='NUM',
            help="Number of processes to use to run tests.  Note that your "
            "tests need to be written to avoid using the same resources (temp "
            "files, sockets, ports, etc.) for the multi-process mode to work "
            "well (--initializer and --finalizer can help provision "
            "per-process resources). Default is to run the same number of "
            "processes as your machine has logical CPUs. Note that for a small "
            "number of trivial tests, running everything in a single process "
            "may be faster than the overhead of initializing all the "
            "processes.",
        default=argparse.SUPPRESS))
    store_opt(
        concurrency_args.add_argument('-i', '--initializer', action='store',
            metavar='DOTTED_FUNCTION',
            help="Python function to run inside of a single worker process "
            "before it starts running tests.  This is the way to provision "
            "external resources that each concurrent worker process needs to "
            "have exclusive access to. Specify the function in dotted notation "
            "in a way that will be importable from the location you are "
            "running green from.",
            default=argparse.SUPPRESS))
    store_opt(
        concurrency_args.add_argument('-z', '--finalizer', action='store',
            metavar='DOTTED_FUNCTION',
            help="Same as --initializer, only run at the end of a worker "
            "process's lifetime.  Used to unprovision resources provisioned by "
            "the initializer.",
            default=argparse.SUPPRESS))
    format_args = parser.add_argument_group("Format Options")
    store_opt(format_args.add_argument('-t', '--termcolor', action='store_true',
        help="Force terminal colors on.  Default is to autodetect.",
        default=argparse.SUPPRESS))
    store_opt(
        format_args.add_argument('-T', '--notermcolor', action='store_true',
        help="Force terminal colors off.  Default is to autodetect.",
        default=argparse.SUPPRESS))
    store_opt(
        format_args.add_argument('-W', '--disable-windows', action='store_true',
        help="Disable Windows support by turning off Colorama",
        default=argparse.SUPPRESS))

    out_args = parser.add_argument_group("Output Options")
    store_opt(out_args.add_argument('-a', '--allow-stdout', action='store_true',
        help=("Instead of capturing the stdout and stderr and presenting it in "
        "the summary of results, let it come through."),
        default=argparse.SUPPRESS))
    store_opt(out_args.add_argument('-q', '--quiet-stdout', action='store_true',
        help=("Instead of capturing the stdout and stderr and presenting it in "
        "the summary of results, discard it completly for successful tests. "
        "--allow-stdout option overrides it."),
        default=argparse.SUPPRESS))
    store_opt(out_args.add_argument('-k', '--no-skip-report',
        action='store_true', help=("Don't print the report of skipped tests "
        "after testing is done.  Skips will still show up in the progress "
        "report and summary count."),
        default=argparse.SUPPRESS))
    store_opt(out_args.add_argument('-h', '--help', action='store_true',
        help="Show this help message and exit.",
        default=argparse.SUPPRESS))
    store_opt(out_args.add_argument('-V', '--version', action='store_true',
        help="Print the version of Green and Python and exit.",
        default=argparse.SUPPRESS))
    store_opt(out_args.add_argument('-l', '--logging', action='store_true',
        help="Don't configure the root logger to redirect to /dev/null, "
        "enabling internal debugging output", default=argparse.SUPPRESS))
    store_opt(out_args.add_argument('-d', '--debug', action='count',
        help=("Enable internal debugging statements.  Implies --logging.  Can "
        "be specified up to three times for more debug output."),
        default=argparse.SUPPRESS))
    store_opt(out_args.add_argument('-v', '--verbose', action='count',
        help=("Verbose. Can be specified up to three times for more verbosity. "
        "Recommended levels are -v and -vv."), default=argparse.SUPPRESS))

    other_args = parser.add_argument_group("Other Options")
    store_opt(other_args.add_argument('-f', '--failfast', action='store_true',
        help=("Stop execution at the first test that fails, errors, or "
        "unexpectedly succeeds."), default=argparse.SUPPRESS))
    store_opt(other_args.add_argument('-c', '--config', action='store',
        metavar='FILE', help="Use this config file instead of the one pointed "
        "to by environment variable GREEN_CONFIG or the default ~/.green",
        default=argparse.SUPPRESS))
    store_opt(other_args.add_argument('-p', '--file-pattern', action='store',
        metavar='PATTERN',
        help="Pattern to match test files. Default is test*.py",
        default=argparse.SUPPRESS))
    store_opt(other_args.add_argument('-n', '--test-pattern', action='store',
        metavar='PATTERN', help="Pattern to match test method names after "
        "'test'.  Default is '*', meaning match methods named 'test*'.",
        default=argparse.SUPPRESS))

    cov_args = parser.add_argument_group(
        "Coverage Options ({})".format(coverage_version))
    store_opt(cov_args.add_argument('-r', '--run-coverage', action='store_true',
        help=("Produce coverage output."), default=argparse.SUPPRESS))
    store_opt(cov_args.add_argument('-O', '--clear-omit', action='store_true',
        help=("Green tries really hard to set up a good list of patterns of "
            "files to omit from coverage reports.  If the default list catches "
            "files that you DO want to cover you can specify this flag to "
            "leave the default list empty to start with.  You can then add "
            "patterns back in with --omit-add. The default list is something"
            "like'*/test*,*/termstyle*,*/mock*,*(temp dir)*,*(python system "
            "packages)*' -- only longer."),
        default=argparse.SUPPRESS))
    store_opt(cov_args.add_argument('-u', '--include-patterns', action='store',
        metavar='PATTERN',
        help=("Comma-separated file-patterns to includie in coverage.  This "
            "implies that anything that does not match the include pattern is "
            "omitted from coverage reporting.  Note that the pattern needs to "
            "match an entire relative path, including a file extension, even "
            "though coverage 4.x doesn't show the file extension."),
        default=argparse.SUPPRESS))
    store_opt(cov_args.add_argument('-o', '--omit-patterns', action='store',
        metavar='PATTERN',
        help=("Comma-separated file-patterns to omit from coverage.  For "
            "example, if coverage reported a file mypackage/foo/bar you could"
            "omit it from coverage with 'mypackage*', '*/foo/*', or '*bar'"),
        default=argparse.SUPPRESS))

    integration_args = parser.add_argument_group("Integration Options")
    store_opt(integration_args.add_argument('--completion-file',
        action='store_true', help=("Location of the bash- and zsh-completion "
            "file.  To enable bash- or zsh-completion, see ENABLING SHELL "
            "COMPLETION below."), default=argparse.SUPPRESS))
    store_opt(integration_args.add_argument('--completions',
        action='store_true',
        help=("Output possible completions of the given target.  Used by bash- "
        "and zsh-completion."), default=argparse.SUPPRESS))
    store_opt(integration_args.add_argument('--options', action='store_true',
        help="Output all options.  Used by bash- and zsh-completion.",
        default=argparse.SUPPRESS))

    args = parser.parse_args()

    # Add additional members
    args.parser    = parser
    args.store_opt = store_opt

    return args


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
def getConfig(filepath=None): # pragma: no cover
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
def mergeConfig(args, testing=False): # pragma: no cover
    """
    I take in a namespace created by the ArgumentParser in cmdline.main() and
    merge in options from configuration files.  The config items only replace
    argument items that are set to default value.

    Returns: I return a new argparse.Namespace, adding members:
        shouldExit       = default False
        exitCode         = default 0
        include patterns = include-patterns setting converted to list.
        omit_patterns    = omit-patterns settings converted to list and
                           extended, taking clear-omit into account.
        cov              = coverage object default None
    """
    config = getConfig(getattr(args, 'config', default_args.config))
    new_args = copy.deepcopy(default_args) # Default by default!

    for name, default_value in dict(default_args._get_kwargs()).items():
        # Config options overwrite default options
        config_getter = None
        if name in ['termcolor', 'notermcolor', 'allow_stdout', 'quiet_stdout',
                'help', 'logging', 'version', 'failfast', 'run_coverage',
                'options', 'completions', 'completion_file', 'clear_omit',
                'no_skip_report', 'disable_windows']:
            config_getter = config.getboolean
        elif name in ['processes', 'debug', 'verbose']:
            config_getter = config.getint
        elif name in ['file_pattern', 'finalizer', 'initializer',
            'include_patterns', 'omit_patterns', 'warnings', 'test_pattern']:
            config_getter = config.get
        elif name in ['targets', 'help', 'config']:
            pass # Some options only make sense coming on the command-line.
        elif name in ['store_opt', 'parser']:
            pass # These are convenience objects, not actual settings
        else:
            raise NotImplementedError(name)

        if config_getter:
            try:
                config_value = config_getter('green', name.replace('_','-'))
                setattr(new_args, name, config_value)
            except (configparser.NoSectionError, configparser.NoOptionError):
                pass

        # Command-line values overwrite defaults and config values when
        # specified
        args_value = getattr(args, name, 'unspecified')
        if args_value != 'unspecified':
            setattr(new_args, name, args_value)

    new_args.shouldExit = False
    new_args.exitCode = 0
    new_args.cov = None

    # Help?
    if new_args.help: # pragma: no cover
        new_args.parser.print_help()
        new_args.shouldExit = True
        return new_args

    # Did we just print the version?
    if new_args.version:
        from green.version import pretty_version
        sys.stdout.write(pretty_version()+'\n')
        new_args.shouldExit = True
        return new_args

    # Handle logging options
    if new_args.debug:
        logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s %(levelname)9s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S")
    elif not new_args.logging:
        logging.basicConfig(filename=os.devnull)

    # Disable termcolor?
    if new_args.notermcolor:
        new_args.termcolor = False

    # Coverage.  We must enable it here because we cannot cover module-level
    # code after it is imported, and this is the earliest place we can turn on
    # coverage.
    omit_patterns = [
        '*/argparse*',
        '*/colorama*',
        '*/django/*',
        '*/distutils*',       # Gets pulled in on Travis-CI CPython
        '*/extras*',          # pulled in by testtools
        '*/linecache2*',      # pulled in by testtools
        '*/mimeparse*',       # pulled in by testtools
        '*/mock*',
        '*/pbr*',             # pulled in by testtools
        '*/pkg_resources*',   # pulled in by django
        '*/pypy*',
        '*/pytz*',            # pulled in by django
        '*/six*',             # pulled in by testtools
        '*/termstyle*',
        '*/test*',
        '*/traceback2*',      # pulled in by testtools
        '*/unittest2*',       # pulled in by testtools
        '*Python.framework*', # OS X system python
        '*site-packages*',    # System python for other OS's
        tempfile.gettempdir() + '*',
    ]
    if new_args.clear_omit:
        omit_patterns = []
    if new_args.omit_patterns:
        omit_patterns.extend(new_args.omit_patterns.split(','))
    new_args.omit_patterns = omit_patterns

    if new_args.include_patterns:
        new_args.include_patterns = new_args.include_patterns.split(',')
    else:
        new_args.include_patterns = []

    if new_args.run_coverage:
        if not coverage:
            print(
                "Fatal: The 'coverage' module is not installed.  Have you "
                "run 'pip install coverage' ???")
            args.shouldExit = True
            args.exitCode = 3
            return args
        if not testing:
            cov = coverage.coverage(data_file='.coverage', omit=omit_patterns,
                    include=new_args.include_patterns)
            cov.start()
        new_args.cov = cov

    return new_args
