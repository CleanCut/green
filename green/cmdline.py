from __future__ import unicode_literals
import os
import sys

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
    if getattr(args, 'html', False): # pragma: no cover
        print("""
The --html flag is scheduled to be removed in version 2.0 due to it being a pain
to maintain and no one using it.  If you actually use it, please open an issue
stating so!  https://github.com/CleanCut/green/issues/new  Unless some people
request it, it will be removed in 2.0
""")
        import time
        time.sleep(2)
    if args.shouldExit:
        return args.exitCode

    # Clear out all the passed-in-options just in case someone tries to run a
    # test that assumes sys.argv is clean.  I can't guess at the script name
    # that they want, though, so we'll just leave ours.
    sys.argv = sys.argv[:1]

    # Set up our various main objects
    from green.loader import loadTargets
    from green.runner import run
    from green.output import GreenStream, debug
    import green.output
    from green.suite import GreenTestSuite
    GreenTestSuite.args = args

    if args.debug:
        green.output.debug_level = args.debug

    stream = GreenStream(sys.stdout, html = args.html)

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

    # Discover/Load the test suite
    if testing:
        test_suite = None
    else:
        test_suite = loadTargets(args.targets, file_pattern = args.file_pattern)

    # We didn't even load 0 tests...
    if not test_suite:
        debug(
            "No test loading attempts succeeded.  Created an empty test suite.")
        test_suite = GreenTestSuite()

    # Actually run the test_suite
    if testing:
        result = lambda: None
        result.wasSuccessful = lambda: 0
    else:
        result = run(test_suite, stream, args) # pragma: no cover

    if args.run_coverage and ((not testing) or coverage_testing):
        stream.writeln()
        args.cov.stop()
        args.cov.save()
        args.cov.combine()
        args.cov.save()
        args.cov.report(file=stream, omit=args.omit_patterns)
    return(int(not result.wasSuccessful()))



if __name__ == '__main__': # pragma: no cover
    sys.exit(main())
