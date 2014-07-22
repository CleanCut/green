from __future__ import unicode_literals
import argparse
import logging
import os
import sys
import tempfile
import unittest

try: # pragma: no cover
    import coverage
    coverage_version = "Coverage {}".format(coverage.__version__)
except: # pragma: no cover
    coverage = None
    coverage_version = "Coverage Not Installed"

# Importing from green is done after coverage initialization

# Set the defaults in a re-usable way
default_args = argparse.Namespace(
        targets      = ['.'], # Not in configs
        subprocesses = 1,
        html         = False,
        termcolor    = None,
        notermcolor  = None,
        debug        = 0,
        help         = False, # Not in configs
        logging      = False,
        version      = False,
        verbose      = 1,
        config       = None,  # Not in configs
        run_coverage = False,
        omit         = None,
        options      = False,
        completions  = False,
        )



class StoreOpt():


    def __init__(self):
        self.options = []
        self.options = []


    def __call__(self, action):
        self.options.extend(action.option_strings[0:2])



def main(testing=False, coverage_testing=False):
    store_opt = StoreOpt()
    parser = argparse.ArgumentParser(
            add_help=False,
            description=
"""
Green is a clean, colorful test runner for Python unit tests.
""".rstrip(),
            epilog=
"""
CONFIG FILES

  Green will look for and process three config files if found:
  1) $HOME/.green
  2) $GREEN_CONFIG
  3) A file specified with "--config FILE"

  Config file format is simply "option = value" on separate lines.  "option" is
  the same as the long options above, just without the "--".

  Most values should be "True" or "False".  Accumulated values (verbose, debug) should
  be specified as integers ("-vv" would be "verbose = 2").

  Example:

    verbose = 2
    logging = True
    omit    = myproj*,*prototype*
""".rstrip(),
            formatter_class=argparse.RawDescriptionHelpFormatter)
    target_args = parser.add_argument_group("Target Specification")
    target_args.add_argument('targets', action='store', nargs='*',
        help=("""Targets to test.  If blank, then discover all testcases in the
        current directory tree.  Can be a directory (or package), file (or
        module), or fully-qualified 'dotted name' like
        proj.tests.test_things.TestStuff.  If a directory (or package)
        is specified, then we will attempt to discover all tests under the
        directory (even if the directory is a package and the tests would not
        be accessible through the package's scope).  In all other cases,
        only tests accessible from introspection of the object will be
        loaded."""))
    concurrency_args = parser.add_argument_group("Concurrency Options")
    store_opt(
        concurrency_args.add_argument('-s', '--subprocesses', action='store',
            type=int, metavar='NUM',
            help="Number of subprocesses to use to run tests.  Note that your "
            "tests need to be written to avoid using the same resources (temp "
            "files, sockets, ports, etc.) for the multi-process mode to work "
            "well. Default is 1, meaning try to autodetect the number of CPUs "
            "in the system.  1 will disable using subprocesses.  Note that for "
            "trivial tests (tests that take < 1ms), running everything in a "
            "single process may be faster."))
    format_args = parser.add_argument_group("Format Options")
    store_opt(format_args.add_argument('-m', '--html', action='store_true',
        help="HTML5 format.  Overrides terminal color options if specified."))
    store_opt(format_args.add_argument('-t', '--termcolor', action='store_true',
        help="Force terminal colors on.  Default is to autodetect."))
    store_opt(
        format_args.add_argument('-T', '--notermcolor', action='store_true',
        help="Force terminal colors off.  Default is to autodetect."))
    out_args = parser.add_argument_group("Output Options")
    store_opt(out_args.add_argument('-d', '--debug', action='count',
        help=("Enable internal debugging statements.  Implies --logging.  Can "
        "be specified up to three times for more debug output.")))
    store_opt(out_args.add_argument('-h', '--help', action='store_true',
        help="Show this help message and exit."))
    store_opt(out_args.add_argument('-l', '--logging', action='store_true',
        help="Don't configure the root logger to redirect to /dev/null, "
        "enabling internal debugging output"))
    store_opt(out_args.add_argument('-V', '--version', action='store_true',
        help="Print the version of Green and Python and exit."))
    store_opt(out_args.add_argument('-v', '--verbose', action='count',
        help=("Verbose. Can be specified up to three times for more verbosity. "
        "Recommended levels are -v and -vv.")))
    other_args = parser.add_argument_group("Other Options")
    store_opt(other_args.add_argument('-c', '--config', action='store',
        metavar='FILE', help="Use this config file instead of the one pointed "
        "to by environment variable GREEN_CONFIG or the default ~/.green"))
    cov_args = parser.add_argument_group(
        "Coverage Options ({})".format(coverage_version))
    store_opt(cov_args.add_argument('-r', '--run-coverage', action='store_true',
        help=("Produce coverage output.")))
    store_opt(cov_args.add_argument('-o', '--omit', action='store',
        metavar='PATTERN',
        help=("Comma-separated file-patterns to omit from coverage.  Default "
            "is something like '*/test*,*/termstyle*,*/mock*,*(temp "
            "dir)*,*(python system packages)*'")))
    parser.set_defaults(**(dict(default_args._get_kwargs())))
    # These options are used by bash-completion and zsh completion.
    parser.add_argument('--options', action='store_true', default=False,
            help=argparse.SUPPRESS)
    parser.add_argument('--completions', action='store_true', default=False,
            help=argparse.SUPPRESS)

    args = parser.parse_args()

    # Unfortunately we can't fully cover the config module (the global part of
    # it), because we need to use it to see if we need to turn coverage on.
    import green.config as config
    args = config.merge_config(args, default_args)

    # Clear out all the passed-in-options just in case someone tries to run a
    # test that assumes sys.argv is clean.  I can't guess at the script name
    # that they want, though, so we'll just leave ours.
    sys.argv = sys.argv[:1]

    # Help?
    if args.help: # pragma: no cover
        parser.print_help()
        return 0

    # Just print version and exit?
    if args.version:
        from green.version import pretty_version
        sys.stdout.write(pretty_version()+'\n')
        return 0

    # Handle logging options
    if args.debug:
        logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s %(levelname)9s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S")
    elif not args.logging:
        logging.basicConfig(filename=os.devnull)

    # These options both disable termcolor
    if args.html or args.notermcolor:
        args.termcolor = False

    # Coverage?
    omit = []
    if args.run_coverage:
        if args.omit:
            omit = args.omit.split(',')
        else:
            omit = [
                '*/test*',
                '*/termstyle*',
                '*/colorama*',
                '*/mock*',
                tempfile.gettempdir() + '*']
            if 'green' not in args.targets and (
                    False in [t.startswith('green.') for t in args.targets]):
                omit.extend([
                '*Python.framework*',
                '*site-packages*'])
        if not coverage:
            sys.stderr.write(
                "Fatal: The 'coverage' module is not installed.  Have you "
                "run 'pip install coverage'???")
            return 3
        if (not testing) or coverage_testing:
            cov = coverage.coverage(data_file='.coverage', omit=omit)
            cov.start()

    # Set up our various main objects
    from green.loader import loadTargets
    from green.runner import GreenTestRunner
    from green.output import GreenStream, debug
    import green.output
    if args.debug:
        green.output.debug_level = args.debug

    stream = GreenStream(sys.stderr, html = args.html)
    runner = GreenTestRunner(verbosity = args.verbose, stream = stream,
            termcolor=args.termcolor, subprocesses=args.subprocesses,
            run_coverage=args.run_coverage, omit=omit)

    # Option-completion for bash and zsh
    if args.options:
        print(' '.join(store_opt.options))
        return 0

    # Argument-completion for bash and zsh (for test-target completion)
    if args.completions:
        from green.loader import printCompletions
        printCompletions(args.targets)
        return 0

    # Add debug logging for stuff that happened before this point here
    if config.files_loaded:
        debug("Loaded config file(s): {}".format(
            ', '.join(config.files_loaded)))

    # Discover/Load the TestSuite
    if testing:
        test_suite = None
    else:
        test_suite = loadTargets(args.targets)

    # We didn't even load 0 tests...
    if not test_suite:
        debug(
            "No test loading attempts succeeded.  Created an empty test suite.")
        test_suite = unittest.suite.TestSuite()

    # Actually run the test_suite
    if testing:
        result = lambda: None
        result.wasSuccessful = lambda: 0
    else:
        result = runner.run(test_suite) # pragma: no cover

    if args.run_coverage and ((not testing) or coverage_testing):
        stream.writeln()
        cov.stop()
        cov.save()
        cov.combine()
        cov.save()
        cov.report(file=stream, omit=omit)
    return(int(not result.wasSuccessful()))



if __name__ == '__main__': # pragma: no cover
    sys.exit(main())
