import argparse
import importlib
import logging
import os
import sys
import tempfile
import unittest

try:
    import coverage
except:
    coverage = None

# Importing from green is done after coverage initialization


def main():
    parser = argparse.ArgumentParser(
            usage="%(prog)s [-hlv] [-m | -t | -T] [target]",
            description="Green is a clean, colorful test runner for Python unit tests.")
    parser.add_argument('target', action='store', nargs='?', default='.',
        help=("""Target to test.  If blank, then discover all testcases in the
        current directory tree.  Can be a directory (or package), file (or
        module), or fully-qualified 'dotted name' like
        proj.tests.test_things.TestStuff.  If a directory (or package)
        is specified, then we will attempt to discover all tests under the
        directory (even if the directory is a package and the tests would not
        be accessible through the package's scope).  In all other cases,
        only tests accessible from introspection of the object will be
        loaded."""))
    parser.add_argument('-V', '--version', action='store_true', default=False,
        help="Print the version of Green and Python and exit.")
    parser.add_argument('-d', '--debug', action='count', default=0,
        help=("Enable internal debugging statements.  Implies --logging.  Can "
        "be specified up to three times for more debug output."))
    parser.add_argument('-l', '--logging', action='store_true', default=False,
        help="Don't configure the root logger to redirect to /dev/null")
    parser.add_argument('-v', '--verbose', action='count', default=1,
        help=("Verbose. Can be specified up to three times for more verbosity. "
        "Recommended levels are -v and -vv."))
    output = parser.add_mutually_exclusive_group()
    output.add_argument('-m', '--html', action='store_true', default=False,
        help="Output in HTML5.  Overrides terminal color options if specified.")
    output.add_argument('-t', '--termcolor', action='store_true', default=None,
        help="Force terminal colors on.  Default is to autodetect.")
    output.add_argument('-T', '--notermcolor', action='store_true', default=None,
        help="Force terminal colors off.  Default is to autodetect.")
    parser.add_argument('-r', '--run-coverage', action='store_true',
        default=False,
        help=("Produce coverage output.  You need to install the 'coverage' "
        "module separately for this to work."))
    args = parser.parse_args()

    # Clear out all the passed-in-options just in case someone tries to run a
    # test that assumes sys.argv is clean.  I can't guess at the script name
    # that they want, though, so we'll just leave ours.
    sys.argv = sys.argv[:1]

    # Just print version and exit?
    if args.version:
        from green.version import pretty_version
        print(pretty_version())
        sys.exit()

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
        if not coverage:
            sys.stderr.write(
                "Fatal: The 'coverage' module is not installed.  Have you "
                "run 'pip install coverage'???")
            sys.exit(3)
        cov = coverage.coverage()
        cov.start()


    # Set up our various main objects
    from green.loader import getTests
    from green.runner import GreenTestRunner, GreenStream, Colors, debug_level
    if args.debug:
        debug_level = args.debug

    colors = Colors(termcolor = args.termcolor, html = args.html)
    stream = GreenStream(sys.stderr, html = args.html)
    runner = GreenTestRunner(verbosity = args.verbose, stream = stream,
            colors = colors)

    # Discover/Load the TestSuite
    tests  = getTests(args.target)

    # We didn't even load 0 tests...
    if not tests:
        logging.debug(
            "No test loading attempts succeeded.  Created an empty test suite.")
        tests = unittest.suite.TestSuite()

    # Actually run the tests
    result = runner.run(tests)
    if args.run_coverage:
        stream.writeln()
        cov.stop()
        omit = [
            '*/test*',
            '*site-packages/pkg_resources*',
            '*Python.framework*',
            tempfile.gettempdir() + '*']
        if 'termstyle' not in args.target:
            omit.append('*/termstyle*')
        if (args.target != 'green') and (not args.target.startswith('green.')):
            omit.append('*site-packages*/green*')
        cov.report(file=stream, omit=omit)
    sys.exit(not result.wasSuccessful())

