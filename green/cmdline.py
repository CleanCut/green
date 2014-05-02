import argparse
import importlib
import os
import sys
import unittest

from green.runner import GreenTestRunner, GreenStream, Colors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('discover_path', action='store', nargs='?', default='.')
    parser.add_argument('-v', '--verbose', action='count', default=1)
    parser.add_argument('-t', '--termcolor', action='store_true', default=None)
    parser.add_argument('-n', '--notermcolor', action='store_true', default=None)
    parser.add_argument('-l', '--html', action='store_true', default=False)
    args = parser.parse_args()

    # These options disable termcolor
    if args.html or args.notermcolor:
        args.termcolor = False

    # Set up our various main objects
    colors = Colors(termcolor = args.termcolor, html = args.html)
    stream = GreenStream(sys.stderr, html = args.html)
    runner = GreenTestRunner(verbosity = args.verbose, stream = stream,
            colors = colors)
    loader = unittest.TestLoader()

    # Actually load the tests
    while True:
        tests = None

        # A directory (some/dir)
        if os.path.isdir(args.discover_path):
            tests = loader.discover(args.discover_path)
            break

        # A directory separated by dots (some.dir)
        dotted_path = args.discover_path.replace('.', os.sep)
        if os.path.isdir(dotted_path):
            tests = loader.discover(dotted_path)
            break

        # Dotted object (package, package.module, package.module.class, etc.)
        try:
            tests = loader.loadTestsFromName(args.discover_path)
        except ImportError:
            pass

        # Python file (package/module.py)
        if os.path.isfile(args.discover_path):
            module = args.discover_path.replace('.py', '').replace(os.sep, '.')
            module = importlib.import_module(module)
            tests = loader.loadTestsFromModule(module)


        # File missing .py (package/module, package/module/submodule)
        try:
            slashed_path = args.discover_path.replace(os.sep, '.')
            tests = loader.loadTestsFromName(slashed_path)
        except (ImportError, AttributeError):
            pass

        break

    # We didn't even load 0 tests...
    if not tests:
        stream.writeln(
            colors.red("Sorry, I couldn't process '{}'.".format(
                args.discover_path)) +
            "  Maybe you should try the --help option?")
        sys.exit(2)

    # Actually run the tests
    result    = runner.run(tests)
    sys.exit(not result.wasSuccessful())

