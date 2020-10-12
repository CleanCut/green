from __future__ import unicode_literals
import os
import sys
import tempfile

# Importing from green (other than config) is done after coverage initialization
import green.config as config


def _main(argv, testing):
    args = config.parseArguments(argv)
    args = config.mergeConfig(args, testing)

    if args.shouldExit:
        return args.exitCode

    # Clear out all the passed-in-options just in case someone tries to run a
    # test that assumes sys.argv is clean.  I can't guess at the script name
    # that they want, though, so we'll just leave ours.
    sys.argv = sys.argv[:1]

    # Set up our various main objects
    from green.loader import GreenTestLoader, getCompletions
    from green.runner import run
    from green.output import GreenStream, debug
    import green.output
    from green.suite import GreenTestSuite

    GreenTestSuite.args = args

    if args.debug:
        green.output.debug_level = args.debug

    stream = GreenStream(sys.stdout, disable_windows=args.disable_windows)

    # Location of shell completion file
    if args.completion_file:
        print(os.path.join(os.path.dirname(__file__), "shell_completion.sh"))
        return 0

    # Argument-completion for bash and zsh (for test-target completion)
    if args.completions:
        print(getCompletions(args.targets))
        return 0

    # Option-completion for bash and zsh
    if args.options:
        print("\n".join(sorted(args.store_opt.options)))
        return 0

    # Add debug logging for stuff that happened before this point here
    if config.files_loaded:
        debug("Loaded config file(s): {}".format(", ".join(config.files_loaded)))

    # Discover/Load the test suite
    if testing:
        test_suite = None
    else:  # pragma: no cover
        loader = GreenTestLoader()
        test_suite = loader.loadTargets(args.targets, file_pattern=args.file_pattern)

    # We didn't even load 0 tests...
    if not test_suite:
        debug("No test loading attempts succeeded.  Created an empty test suite.")
        test_suite = GreenTestSuite()

    # Actually run the test_suite
    result = run(test_suite, stream, args, testing)

    # Generate a test report if required
    if args.junit_report:
        from green.junit import JUnitXML

        adapter = JUnitXML()
        with open(args.junit_report, "w") as report_file:
            adapter.save_as(result, report_file)

    return int(not result.wasSuccessful())


def main(argv=None, testing=False):
    # create the temp dir only once (i.e., not while in the recursed call)
    if os.environ.get("TMPDIR") is None:  # pragma: nocover
        with tempfile.TemporaryDirectory() as temp_dir_for_tests:
            try:
                os.environ["TMPDIR"] = temp_dir_for_tests
                tempfile.tempdir = temp_dir_for_tests
                return _main(argv, testing)
            finally:
                del os.environ["TMPDIR"]
                tempfile.tempdir = None
    else:
        return _main(argv, testing)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
