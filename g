#!/usr/bin/env python3

import argparse
import os
import sys
import unittest

from green.runner import GreenTestRunner, GreenStream, Colors

if __name__ == '__main__':
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
        print(args.termcolor)

    # Set up our various main objects
    colors    = Colors(termcolor = args.termcolor, html = args.html)
    stream    = GreenStream(sys.stderr, html = args.html)
    runner    = GreenTestRunner(verbosity = args.verbose, stream = stream,
            colors = colors)
    loader    = unittest.TestLoader()

    # Actually load the tests
    while True:
        tests = None

        if os.path.isdir(args.discover_path):
            tests = loader.discover(args.discover_path)
            break

        dotted_path = args.discover_path.replace('.', os.sep)
        if os.path.isdir(dotted_path):
            tests = loader.discover(dotted_path)
            break

        try:
            tests = loader.loadTestsFromName(args.discover_path)
        except ImportError:
            pass
        break

    if not tests:
        stream.writeln(
                colors.red("Couldn't find anything to test.") +
                "  Maybe you should try the --help option?")
        sys.exit(2)

    result    = runner.run(tests)
    sys.exit(not result.wasSuccessful())
