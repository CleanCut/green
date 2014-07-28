from __future__ import unicode_literals
import os
import sys
import unittest

try: # pragma: no cover
    import coverage
    coverage_version = "Coverage {}".format(coverage.__version__)
except: # pragma: no cover
    coverage = None
    coverage_version = "Coverage Not Installed"

# Importing from green (other than config) is done after coverage initialization
import green.config as config



def main(testing=False, coverage_testing=False):
    args = config.parseArguments()
    args = config.mergeConfig(args, testing, coverage_testing)
    if args.shouldExit:
        return args.exitCode

    # Clear out all the passed-in-options just in case someone tries to run a
    # test that assumes sys.argv is clean.  I can't guess at the script name
    # that they want, though, so we'll just leave ours.
    sys.argv = sys.argv[:1]

    # Set up our various main objects
    from green.loader import loadTargets
    from green.runner import GreenTestRunner
    from green.output import GreenStream, debug
    import green.output
    if args.debug:
        green.output.debug_level = args.debug

    stream = GreenStream(sys.stdout, html = args.html)
    runner = GreenTestRunner(verbosity = args.verbose, stream = stream,
            termcolor=args.termcolor, subprocesses=args.subprocesses,
            run_coverage=args.run_coverage, omit=args.omit)

    # Location of shell completion file
    if args.completion_file:
        print(os.path.join(os.path.dirname(__file__), 'shell_completion.sh'))
        return 0

    # Argument-completion for bash and zsh (for test-target completion)
    if args.completions:
        from green.loader import getCompletions
        print(getCompletions(args.targets))
        return 0

    # Option-completion for bash and zsh
    if args.options:
        print('\n'.join(sorted(args.store_opt.options)))
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
        args.cov.stop()
        args.cov.save()
        args.cov.combine()
        args.cov.save()
        args.cov.report(file=stream, omit=args.omit)
    return(int(not result.wasSuccessful()))



if __name__ == '__main__': # pragma: no cover
    sys.exit(main())
