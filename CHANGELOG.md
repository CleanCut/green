# Version 1.9.4
##### 15 June 2015

- Added a deprecation warning for the `-m/--html` option.  Unless I get some
  credible requests to leave the functionality, then I am going to proceed with
  removing it under the assumption that no one uses it (and I don't want to
  maintain complex, unused code).
- Investigated an issue with `SystemExit` and `KeyboardInterrupt` halting the
  python process when your test subclasses `testtools.TestCase`.  Turns out
  that that is a design decision made by the testtools devs that they want those
  exceptions to stop everything.  So we won't interfere with their desires.  If
  you don't like the behavior, either stop subclassing `testtools.TestCase` or
  simply catch those two exceptions in your own tests.


# Version 1.9.3
##### 7 June 2015

- Switched to cyan instead of blue on Windows only.
- Stubbed in the beginnings of support for designating initialization to run in
  each process to obtain whatever resources might be needed by a single
  process (like its own database, for example).


# Version 1.9.2
##### 8 May 2015

- Fixed a regression that caused the `-a/--allow-stdout` cli option and
  corresponding config option to be ignored.  Fixes issue #58.


# Version 1.9.1
##### 13 April 2015

- Don't do the interactive print/reprint a test line behavior when we're not
  connected to a terminal.  Contributed by Sam Spilsbury.  Issue #52.  Pull
  request #53.

- Fixed a rather largeish bug that caused all configuration files to be
  ignored.  Issue #56.  Thanks for Monty Hindman for finding and reporting the
  bug.

- The `g` script has been improved so that wildcards are passed through without
  local expansion.  `g` is is used by developers to try out changes to green
  itself in-place without installing it.  Contributed by Monty Hindman.  Pull
  request #57.

- Switch to Travis CI's docker builders for faster builds.  Contributed by Sam
  Spilsbury.  Issue #54.  Pull request #55.

- Cleaned up the formatting of dates on this changelog file.

- Removed Python 3.3 builders on Linux, now that they're failing.  Official
  support for Python 3.3 was dropped on 31 August 2014.  It may still work in
  various use cases, but no guarantees.

- Fixed `test_versions` again.  The regex for non-Travis CI builds had broken,
  so that only the default python was being tested on development setups.


# Version 1.9.0
##### 8 April 2015

- BREAKING CHANGE: `--omit` was renamed to `--omit-patterns` for consistency
  with how other pattern-related options are named.

- BREAKING CHANGE: `--pattern` was renamed to `--file-pattern` for consistency
  with how other pattern-related options are named.

- Added `-n` / `--test-pattern` option to further refine which tests are
  actually run.  Thanks to Monty Hindman for a pull request that got this
  feature going.

- Tweaked Travis CI builds


# Version 1.8.1
##### 1 April 2015 (Not a joke!)

- Fixed issue where command-line arguments could not override config
arguments to set options back to default values.  Reported by Monty Hindman.
Issue #47.

- Converted this changelog file to markdown format.


# Version 1.8.0
##### 30 March 2015

- The tag to use for questions on StackOverflow was changed to python-green to
  avoid being too generic.  The tag has a nice wiki entry and an initial
  question to get things going.  Contributed by Mikko Ohtamaa.  Pull request #43.

- Added `-p/--pattern` option to specify the file pattern to search for
  tests under instead of the default pattern `test*py`. Contributed by Monty
  Hindman.  Issue #41.  Pull request #42.

- Green now supports nose-parameterized.  Contributed by Sam Spilsbury.
  Issue #39.  Pull request #40.

- Fixed a crash that could occur in PyPy 2.5

- Fixed a crash that could occur during automated build testing with pip 6.x

- Colorama is now a dependency on all platforms (dropping python-termstyle as a
  dependency is planned).


# Version 1.7.1
##### 25 November 2014

- When run in completions mode (`green --completions`), import errors in
  potential modules are ignored, so that the completions list is still
  generated instead of producing crash output.


# Version 1.7.0
##### 21 September 2014

- Output sent to stdout is now captured and then presented along with the list
  of tracebacks.  This can be disabled with `-a/--allow-stdout`.  Issue #29.


# Version 1.6.0
##### 10 September 2014

- Added `-f/--failfast` to stop executing tests after the first error, failure,
  or unexpected successes.

- Simplified the usage line in the help output.


# Version 1.5.0
##### 31 August 2014

- You can press Ctrl-C once while tests are running to cleanly terminate the
  test run.

- Some internal refactoring.

- Python 3.3 is no longer supported on Windows.  It might work still--it's just
  not supported.

- Windows CI with AppVeyor is now passing.


# Version 1.4.4
##### 26 August 2014

- File handles are now explicitly closed in setup.py.  Contributed by Simeon
  Visser.


# Version 1.4.3
##### 26 August 2014

- Trying to import a module by name that raises an exception during import now
  manufactures a test that reports an ImportError instead of just silently
  ignoring the file.  Issue #31.


# Version 1.4.2
##### 14 August 2014

- Automated generation of the CLI documentation.
- Improved the suggest command for Bash-/Zsh-completion integration.
- Improved the README file.
- Fixed a crash that could occur if an exception was raised during a test
  case's setUpClass() or tearDownClass()
- We now explicitly terminate the thread pool and join() it.  This makes self
  unit tests much easier to clean up on Windows, where the processes would
  block deletion of temporary directories.
- Set up continuous integration for Windows using AppVeyor.  Thanks to ionelmc
  for the tip!  Issue #11.


# Version 1.4.1
##### 30 July 2014

- We now use the fully-dotted test name at the start of each traceback in the
  error listing.  Issue #28.
- PyPy libraries are now omitted from coverage by default.
- More cleanup on internal tests.


# Version 1.4.0
##### 30 July 2014

### User Stuff

- Django integration!  Issue #21.  There are two ways to use green while
  running Django unit tests:

```
1) To just try it out, use the --testrunner option:
    ./manage.py test --testrunner=green.djangorunner.DjangoRunner
2) Make it persistent by adding the following line to your settings.py:
    TEST_RUNNER=green.djangorunner.DjangoRunner
(Use green config files to customize the output)
```

- Switched from using stderr to stdout.  This makes piping output to another
  program much easier, and reserves stderr for actual errors running green
  itself.

- Improved the exception output when a test module cannot be imported.

### Internal Stuff

- Updated the Travis config to make use of the Makefile

- Updated the Makefile with more and better organized test targets.

- Added a test_versions script that can be run on developer clones.  It will
  auto-detect all versions of python (in the form of pythonX.Y) in $PATH and
  run many permutations of self tests on each version.
- Fixed a crash that could occur if discovery did not find any tests and
  processes was set higher than one.

- Fixed lots of tests so that they would succeed in all environments.

- Internal refactoring of argument parsing and configuration handling.


# Version 1.3.1
##### 23 July 2014

- Fixed the new tests that failed if you ran them in-place on an installed
  version of green.  Forgot to check the build status before I did the last
  release!


# Version 1.3.0
##### 23 July 2014

- Bash-completion and ZSH-completion support for options and test targets.
  Issue #7.


# Version 1.2.1
##### 20 July 2014

- Multiline docstrings (with -vv or -vvv) on test methods are now handled
  correctly.  Initial whitespace is first stripped.  Then lines are combined
  into one space-separated string until the first blank line.  Issue #26.


# Version 1.2.0
##### 20 July 2014

- Implemented custom test discovery code instead of relying on built-in
  unittest.discover(). So far, the new implementation  mimics the built-in
  behavior except for fixing issue #14 (which unblocks #7).  This enables working
  on #25 and any other bugs or behavior that was locked inside of unittest's
  quirky discovery implementation that we want to fix in the future.

- Fixed travis config to exclude the example project in builds.

- Reduced debug timestamp precision from microsecond- to second-based.

- Exclude colorama from coverage reporting for the sake of Windows users.

- Added some additional internal debug output.

- Centralized internal debugging output.

- "make clean" now cleans all `.coverage*` files in the project tree.

- Many new internal tests.


# Version 1.1.0
##### 17 July 2014

- Configuration file support, originally contributed by Tom Barron - Issues
  #20, #23, #24


# Version 1.0.2
##### 6 July 2014

- Color works on Windows - Issues #18, #19

- Self-tests run against installed versions automatically - Issue #10

- Installation process is now tested automatically - Issue #9

- Switched to "branch-based development"

- Added an "example" directory with an example project with unit tests

- Added the CHANGELOG (this file)

- Improved the README.md file a lot based on feedback from reddit.


# Version 1.0.1
##### 23 June 2014

- Fixed MANIFEST so that installation didn't crash


# Version 1.0
##### 22 June 2014

### Features

- Colorful - Terminal output makes good use of color when the terminal supports
  it.

- Clean - Low redundancy in output. Result stats for each test is lined up in a
  vertical column.

- Fast - Can run tests in independent processes.

- Powerful - Multi-target + auto-discovery.

- Traditional - Use the normal `unittest` classes and methods for your unit
  tests.

- Descriptive - Four verbosity levels, from just dots to full docstring output.

- Thorough - Built-in, optional integration with coverage

- Modern - Supports Python 2.7, 3.3, 3.4, and PyPy

- Portable - Completely supports OS X, Linux, and BSDs (and maybe Windows).

- Flexible - Optional HTML output.


# Version (everything before 1.0)

- There were lots of versions before 1.0 was released (54 published releases,
  actually).  No one heard about it before 1.0 though, so we didn't bother
  tracking individual releases.
