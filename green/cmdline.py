import argparse
import importlib
import logging
import os
import sys
import unittest

from green.runner import GreenTestRunner, GreenStream, Colors


def getTests(target):
    loader = unittest.TestLoader()

    # DIRECTORY VARIATIONS - These will discover all tests in a directory
    # structure, whether or not they are accessible by the root package.

    # some/real/dir
    bare_dir = target
    # some.real.dir
    if '.' in target:
        dot_dir  = target.replace('.', os.sep)
    else:
        dot_dir = None
    # pyzmq.tests  (Package (=dir) in PYTHONPATH, including installed ones)
    pkg_in_path_dir = None
    if target and (target[0] != '.'):
        try:
            pkg_in_path_dir = os.path.dirname(
                    importlib.import_module(target).__file__)
        except ImportError:
            pkg_in_path_dir = None

    # => DISCOVER DIRS
    for candidate in [bare_dir, dot_dir, pkg_in_path_dir]:
        if (candidate == None) or (not os.path.isdir(candidate)):
            continue
        tests = loader.discover(candidate)
        if tests and tests.countTestCases():
            return tests


    # DOTTED OBJECT - These will discover a specific object if it is
    # globally importable or importable from the current working directory.
    # Examples: pkg, pkg.module, pkg.module.class, pkg.module.class.func
    tests = None
    try:
        tests = loader.loadTestsFromName(target)
    except ImportError:
        pass
    if tests and tests.countTestCases():
        return tests


    # FILE VARIATIONS - These will import a specific file and any tests
    # accessible from its scope.

    # some/file.py
    bare_file = target
    # some/file
    pyless_file = target + '.py'
    for candidate in [bare_file, pyless_file]:
        if (candidate == None) or (not os.path.isfile(candidate)):
            continue
        try:
            slashed_path = target.replace('.py', '').replace(os.sep, '.')
            tests = loader.loadTestsFromName(slashed_path)
        except (ImportError, AttributeError):
            pass
        if tests.countTestCases():
            return tests


    # INSTALLED MODULE - (Unlike the installed package, we don't discover
    # inaccessible tests in this case -- we stick to tests accessible from the
    # module)
    tests = None
    try:
        module = importlib.import_module(target)
        tests = loader.loadTestsFromModule(module)
    except ImportError:
        pass
    if tests.countTestCases():
        return tests

    return None



def main():
    parser = argparse.ArgumentParser(
            usage="%(prog)s [-hlv] [-m | -t | -T] [target]",
            description="Green provides clean output for Python unit tests.")
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
    args = parser.parse_args()

    if not args.logging:
        logging.basicConfig(filename=os.devnull)

    # These options disable termcolor
    if args.html or args.notermcolor:
        args.termcolor = False

    # Set up our various main objects
    colors = Colors(termcolor = args.termcolor, html = args.html)
    stream = GreenStream(sys.stderr, html = args.html)
    runner = GreenTestRunner(verbosity = args.verbose, stream = stream,
            colors = colors)

    tests = getTests(args.target)

    # We didn't even load 0 tests...
    if not tests:
        stream.writeln(
            colors.red("Sorry, I couldn't process '{}'.".format(
                args.target)) +
            "  Maybe you should try the --help option?")
        sys.exit(2)

    # Actually run the tests
    result    = runner.run(tests)
    sys.exit(not result.wasSuccessful())

