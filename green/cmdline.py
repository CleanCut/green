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


def main(testing=False, coverage_testing=False):
    parser = argparse.ArgumentParser(
            add_help=False,
            description="Green is a clean, colorful test runner for Python unit tests.")
    target_args = parser.add_argument_group("Target Specification")
    target_args.add_argument('targets', action='store', nargs='*', default=['.'],
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
    concurrency_args.add_argument('-s', '--subprocesses', action='store',
            type=int, default=1, metavar='NUM',
            help="Number of subprocesses to use to run tests.  Note that your "
            "tests need to be written to avoid using the same resources (temp "
            "files, sockets, ports, etc.) for the multi-process mode to work "
            "well. Default is 1, meaning try to autodetect the number of CPUs "
            "in the system.  1 will disable using subprocesses.  Note that for "
            "trivial tests (tests that take < 1ms), running everything in a "
            "single process may be faster.")
    format_args = parser.add_argument_group("Format Options")
    format_args.add_argument('-m', '--html', action='store_true', default=False,
        help="HTML5 format.  Overrides terminal color options if specified.")
    format_args.add_argument('-t', '--termcolor', action='store_true',
        default=None,
        help="Force terminal colors on.  Default is to autodetect.")
    format_args.add_argument('-T', '--notermcolor', action='store_true',
        default=None,
        help="Force terminal colors off.  Default is to autodetect.")
    out_args = parser.add_argument_group("Output Options")
    out_args.add_argument('-c', '--config', action='store',
                          default=None,
                          help="Explicit config file")
    out_args.add_argument('-C', '--cfgcheck', action='store_true',
                          default=False,
                          help="Dump the config and exit")
    out_args.add_argument('-d', '--debug', action='count', default=0,
        help=("Enable internal debugging statements.  Implies --logging.  Can "
        "be specified up to three times for more debug output."))
    out_args.add_argument('-h', '--help', action='store_true', default=False,
        help="Show this help message and exit.")
    out_args.add_argument('-l', '--logging', action='store_true', default=False,
        help="Don't configure the root logger to redirect to /dev/null")
    out_args.add_argument('-V', '--version', action='store_true', default=False,
        help="Print the version of Green and Python and exit.")
    out_args.add_argument('-v', '--verbose', action='count', default=1,
        help=("Verbose. Can be specified up to three times for more verbosity. "
        "Recommended levels are -v and -vv."))
    cov_args = parser.add_argument_group(
        "Coverage Options ({})".format(coverage_version))
    cov_args.add_argument('-r', '--run-coverage', action='store_true',
        default=False,
        help=("Produce coverage output."))
    cov_args.add_argument('-o', '--omit', action='store', default=None,
        metavar='PATTERN',
        help=("Comma-separated file-patterns to omit from coverage.  Default "
            "is something like '*/test*,*/termstyle*,*/mock*,*(temp "
            "dir)*,*(python system packages)*'"))
    args = parser.parse_args()

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

    # Check config
    from green.config import get_config, load_config
    load_config(args.config)
    if args.cfgcheck:
        from green.config import get_config
        cfg = get_config()
        cfg.write(sys.stdout)
        return 0

    # Handle logging options
    if args.debug:
        logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s %(levelname)9s %(message)s")
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
                '*/mock*',
                tempfile.gettempdir() + '*']
            if 'green' not in args.targets and (False in [t.startswith('green.') for t in args.targets]):
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
    from green.loader import getTests
    from green.runner import GreenTestRunner
    from green.output import GreenStream
    import green.output
    if args.debug:
        green.output.debug_level = args.debug

    stream = GreenStream(sys.stderr, html = args.html)
    runner = GreenTestRunner(verbosity = args.verbose, stream = stream,
            termcolor=args.termcolor, subprocesses=args.subprocesses,
            run_coverage=args.run_coverage, omit=omit)

    # Discover/Load the TestSuite
    tests = getTests(args.targets)

    # We didn't even load 0 tests...
    if not tests:
        logging.debug(
            "No test loading attempts succeeded.  Created an empty test suite.")
        tests = unittest.suite.TestSuite()

    # Actually run the tests
    if testing:
        result = lambda: None
        result.wasSuccessful = lambda: 0
    else:
        result = runner.run(tests) # pragma: no cover

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
