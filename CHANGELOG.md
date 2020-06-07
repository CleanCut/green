# Version 3.2.0
#### 6 June 2020

- Fix crashes and hangs that could occur when using >1 subprocess due to a regression introduced in 3.1.1.
- Add 'time' attributes to the `<testsuites>`, `<testsuite>`, and `<testcase>` fields in the Junit
  output for the `-j/--junit-report` output.  Contributed by @bkmd11 in #225. Resolves #208.

# Version 3.1.4 - Buggy! Please upgrade to >= 3.2.0!
#### 7 May 2020

- Fix class/module teardowns being ignored. They are now reported as errors as they should be. Resolves #223.
- Fix dates in this changelog--I was still using last year! 😆

# Version 3.1.3 - Buggy! Please upgrade to >= 3.2.0!
#### 5 May 2020

- Fix crash that could occur when whitespace is in the path on Windows.
  Contributed by @bkmd11 in #222.

# Version 3.1.2 - Buggy! Please upgrade to >= 3.2.0!
#### 4 May 2020

- Fix a crash that could occur during cleanup on unusual filesystems on
  Python 2. Note that Python 2 is still not supported...but might as well fix
  stuff if it is easy to fix. :-) Resolves #221.

# Version 3.1.1 - Buggy! Please upgrade to >= 3.2.0!
#### 22 April 2020

- Fixed a hang that sometimes occurs in Python 3.8.0-3.8.2 due to a bug in upstream Python
  - Upstream bug report: https://bugs.python.org/issue39360
  - Upstream fix in master: https://github.com/python/cpython/pull/19009
  - Upstream fix in 3.8 branch (Maybe gets included in 3.8.3?): https://github.com/python/cpython/pull/19023
- Fixed behavior of raising SkipTest in a setUpClass class method on Python >= 3.8

# Version 3.1.0
#### 3 Jan 2020

- You can now financially support Green by sponsoring @CleanCut at
  https://github.com/sponsors/CleanCut

- Added support for DocTests.  I got interested in why @charles-l's attempt to
  crash instead of hang when doctests were encountered didn't work, and ended
  up just adding support as a feature.  To parse/run doctests for a particular
  module, in a _test_ module add `doctest_modules = [ ... ]` where each item
  is (preferably) an imported module or a dotted string representing a module
  to be imported that contains tests in docstrings.  Resolves #88, #214.

- Fixed a crash and a test failure that could occur with Coverage 5.x

- Updated TravisCI builds with Python 3.8 on Linux and Xcode 11.3 on macOS.

# Version 3.0.0
#### 26 Aug 2019

- Dropped support for Python 2.7.  Green might still continue working on 2.7,
  and I'll accept patches to keep it working if anyone submits them, but I'm
  removing 2.7 from the test matrix.  Ten years ago I thought this day would
  never come...but it finally has!

- Fixed handling of green 'verbose' Django args. Contributed by @mammadori
  in #209.

# Version 2.16.1
#### 29 Apr 2019

- Fixed a crash that could occur when attempting to load tests from files that
  Green lacks permissions to access.  Contributed by @jrabbit in #205.

# Version 2.16.0
#### 25 Apr 2019

- Added `-m/--minimum-coverage` to print a message and exit nonzero if a
  certain coverage percentage isn't met. Resolves #135.
- Added `-g/--cov-config-file` to pass through a custom coverage config file
  location.  Note that if you do not specify this option, coverage already
  looks for its config files in the standard locations, this just adds the
  option to specify a specific, custom config file. Resolves #168.

# Version 2.15.0
#### 11 Apr 2019

- Added `-j/--junit-report` to generate an JUnit/XML test report.
  Contributed by @fchauvel in #204. Resolves #104.

# Version 2.14.2
#### 4 Apr 2019

- Add an .encoding attribute to the wrapped sys.stdout so that things like
  z3 which expect it to be present don't crash. Resolves #203.

# Version 2.14.1
#### 21 Mar 2019

- Removed a redundant optional dependency that was already a required
  dependency.  Thanks to @AndreGuerra123, @GjjvdBurg, and @yelectric for
  researching this.  Resolves #202.

# Version 2.14.0
#### 15 Mar 2019

- Added `-U/--disable-unidecode` to disable using unidecode to convert test
  output from unicode to ascii on Windows. Note that this conversion was
  done to work around some difficult-to-debug crashes on Windows, so using
  this option has a possibility of re-introducing those crashes. Resolves #201.

# Version 2.13.1
#### 11 Feb 2019

- Tested Green with Django 2.1.5 -- it seems to work just fine. Something
  must have changed between Django 2.0.0 and 2.1.5 that eliminated the
  problem we were having.

- Properly close the version file after reading it so it doesn't leave the
  file handle open for the duration of Green running. Contributed by
  Nickolas Grigoriadis in #200.

- Drop official support for Python 3.4, though Green will probably continue to
  work for Python 3.4 for some years before something actually breaks.

- Remove code supporting Python 3.3. We dropped official support in 2015.

- Drop termstyle dependency in favor of using only colorama. Contributed by
  Ogaday in #199 to resolve #186.

- Show number of processes used in test summary. Contributed in #198 by Ogaday
  to resolve #85.

- CI fixes/improvements - the world keeps changing.

- Some typo fixes in README.md and help output

# Version 2.13.0
#### 5 Oct 2018

- Add `-e/--no-tracebacks` to omit traceback output for failures and errors.
  Resolves feature request #191.

- Fixed travis builds

- Documentation updates (readme, release doc), one by Nattaphoom Chaipreecha
  in #192.

- Fix example in `djangorunner.py`. Contributed by Yong Joseph Bakos in #188.

- Tooling fixes, including using python3, twine and keyring to do releases.

# Version 2.12.1
#### 25 Feb 2018

- Switch from python-termstyle (apparently abandoned) to termstyle.  We should
  drop termstyle altogether in favor of colorama (see also #186). Contributed
  by Robert Schüts in #182

- Fix bug that prevented `python setup.py --help-commands` from working
  properly.  Contributed by Martin Larralde in #184.

- Move the config file documentation to the readme file. Contributed by Yuri
  Shikanov in #179.

- Update the TravisCI config and some self-testing procedures to pass updated
  macOS VM builds.

# Version 2.12.0
#### 7 Dec 2017

- Coverage is now required!  Python packages do not support the idea of an
  optional dependency, and having a de-facto optional dependencies was causing
  coverage functionality to be broken for packages who want to use green with
  coverage during `python setup.py test`.  Resolves #174.
- The `test_versions` utility for testing green itself now deduplicates the
  versions of Python it finds, so it only runs one test for Python 2.7, for
  example.  It uses the one it finds first in the $PATH.

# Version 2.11.2
#### 15 Nov 2017

- Fixed temp files not getting properly cleaned up on Windows and Linux in
  Python 3 (problem persists for macOS). Contributed by Martin Larralde in #173.

# Version 2.11.1
#### 25 Oct 2017

- Fixed bug causing several django testing options to be unavailable when using
  green as the test runner for django.  Resolves #172.

# Version 2.11.0
#### 10 Aug 2017

- SubTest context manager support introduced in Python 3.4 is now explicitly
  supported.  In previous versions of Green the SubTests would run correctly,
  but not get reported...sanely.  The bulk of this work was contributed by
  VladV in #167.  Resolves #111.

# Version 2.10.0
#### 8 July 2017

- Green can now be used as a `setup.py` test runner.  See `green --help` or the
  main readme for details.  Contributed by Martin Larralde in #165.  Resolves
  enhancement request #158.

- Lower prices on training course.  Choose your own price.

# Version 2.9.0
#### 23 June 2017

- Green now supports unittest's `load_test` protocol. Contributed by Martin
  Larralde in #160.  Resolves #87.

- Add support for a `[green]` configuration section inside of `setup.cfg` in
  the current working directory.  See the `CONFIG FILES` section of `green
  --help` for a list of relative configuration file priority and how to use them.
  Contributed by Martin Larralde in #161.

- Minor grammar/spelling fixes.

# Version 2.8.2
#### 7 May 2017

- Work around Python's failure to skip tests in a consistent way -- in
  particular, if SkipTest was raised in setUpClass(), then different versions
  of Python did different things, none of them very sensible.  We take the
  approach that Python _should have_ taken and skip each test as the SkipTest
  exception is raised.  This results in one skip entry per test in the class
  that was skipped. Resolves #159.

- Fixed the warning in Python 3.6 due to an inadvertent double-import issue.

- Fixed crash that could occur running self-tests on newer versions of Python
  2.7 which expect to use an iterator with a next() function.


# Version 2.8.1
#### 29 April 2017

- An unexpectedSuccess does not count as a failure for the test run as a whole,
  so `-f, --failfast` has been updated so that an unexpectedSuccess no longer
  triggers early termination. Using @expectedFailure is discouraged.

# Version 2.8.0
#### 27 April 2017

- Green now also searches the current working directory for a .green config
  file.  This can be used as per-project configuration -- just place the .green
  config file for your project in the same directory you would run your tests
  from (usually the root of the project).  See `green --help` for the
  resolution order of the various config files.  Resolves #116.

# Version 2.7.4
#### 26 April 2017

- Added a page about the Udemy course
  [Python Testing with Green](https://github.com/CleanCut/green/blob/master/PythonTestingWithGreen.md),
  with lots of nice coupons and discount codes just for finding the Github
  page.  Check it out!

- PyPy support is now best-effort for all versions of PyPy.  TravisCI's PyPy
  installations are just...flaky.  They seem to work everywhere else, we just
  don't fail due to failing PyPy builds anymore, because we just can't take the
  weirdness.

- Fixed a condition where green could return failure to the calling shell if
  only a small number of skips, expectedFailures, and unexpectedSuccesses were
  run (and no passes, fails, or errors).

- Improved the help message for `-l, --logging`

# Version 2.7.3
#### 24 March 2017

- Fixed a green crash that could occur when dealing with unicode literals in
  raised exceptions under Python 2.

# Version 2.7.2
#### 22 March 2017

- Fixed a corner-case where targets wouldn't be parallelized if you ran green
  inside a directory containing only test modules (files) with no packages
  (directories).  The result would be a single worker process would handle all
  testing while the other worker processes sat idle.

# Version 2.7.1
#### 19 March 2017

- Stop cleaning up the temporary directory on versions of Python other than 2,
  since some things like multiprocess.Value in versions > 2 trigger an
  auto-cleanup of the temporary directory that crashes if it has already been
  cleaned up.  Resolves #154.

- macOS builds on TravisCI have been passing awhile.  Start counting them
  towards global pass/fail.

# Version 2.7.0
#### 2 March 2017

- When used as a Django test runner, we now inject a `--green-verbosity`
  command-line argument that can be used to control green's verbosity level
  from Django.  Contributed by Anomitra Saha.  Resolves #37 and #153.

# Version 2.6.3
#### 20 February 2017

- Switched the release process to use python2 for everything, because python3
  isn't installed in all TravisCI environments.

# Version 2.6.2
#### 20 February 2017

- Fix some minor issues in help strings that I discovered while working on
  "Python Testing with Green"
- Updated the release process so that instead of using a confusing mix of
  python2 and python3 to test and release, we just use python3.

# Version 2.6.1
#### 14 February 2017

- Fixed a bug that caused a strange extra test result to be output when your
  test tried to access a member of an object that didn't exist. Fixes #150.


# Version 2.6.0
#### 22 January 2017

- The `-R, --quiet-coverage` flag can be used to run coverage without printing
  the coverage report to stdout.  Contributed by Martin Larralde. PR #149.
  Resolves feature request #148.


# Version 2.5.3
#### 20 December 2016

- Improved file object compatibility of GreenStream.  Code that now tries to
  access the writelines() function on sys.stdout or sys.stderr should no longer
  crash.  Fixes #146.

- Explicitly tell coverage to include missing line numbers to restore the
  default behavior that changed in coverage 4.1 and later.


# Version 2.5.2
#### 20 October 2016

- Fix crash that would occur on Python 2.7.0, 2.7.1, 2.7.2, and 2.7.3.
  Reported by Christopher Gurnee.  Fixes #137.

- Fix print statements inside of tests on Windows with Python 2.7.  Contributed
  by Christopher Gurnee.  PR #138.

- Remove TravisCI builds for Xcode 7.1, since they no longer support those
  builds.  Unfortunately, the other OS X builds on Travis are broken for some
  reason that doesn't exist on real OS X.  If anyone has any ideas, please
  share.

- Remaining OS X builds on TravisCI are failing right now trying to execute
  PyPy itself (library linking errors).  Since the tests work fine on actual OS
  X installations, I'm going to ignore the failing builds and shake my hand
  furiously at TravisCI.


# Version 2.5.1
#### 30 June 2016

- Expose `green.version.__version__` as `green.__version__`. Reported by Bryant
  Mairs. Fixes #128.

- Fix a crash that could occur if the test loader loaded an unrunnable object.
  Contributed by Eli Skeggs. PR #125.

- Fixed a source of a double-submission bug that was being worked around
  internally.  Contributed by Eli Skeggs.  PR #126.


# Version 2.5.0
#### 31 May 2016

- No tests being loaded is now reported as an error, rather than a pass.  This
  should help people more quickly discover when they have a typo in their
  command-line resulting in no tests being loaded.  Contributed by Douglas
  Thor.  Fixes #123.


# Version 2.4.2
#### 26 May 2016

- On Windows we now mangle non-ascii output into ascii output,
  because...Windows.  Contributed by MinchinWeb.  Fixes #119.

- We now run TravisCI builds for OS X 10.10 and 10.11.  We had already been
  manually running tests on the latest OS X, but now TravisCI will do it for
  us.


# Version 2.4.1
#### 19 May 2016

- The built-in unittest module (stupidly) reports crashes in setUpClass() in a
  completely different way than any other failure or crash in unittest.  Now we
  handle that way.  Fixes #121.


# Version 2.4.0
#### 1 April 2016

- Added `-W/--disable-windows` to disable converting colors to windows format.
  Useful for fake windows terminal environments that want the normal posix
  color codes.  Contributed by Douglas Thor.

- Minor documentation update.  Contributed by Thijs Triemstra.

- Experimented with a coding style contributed by John Vandenberg.  Decided
  we're not yet ready for that much structure.  Maybe someday in the future.


# Version 2.3.0
#### 13 February 2016

- Added `-q/--quiet-stdout` output option.  Instead of capturing the stdout and
  stderr and presenting it in the summary of results, discard it completly for
  successful tests. --allow-stdout option overrides it.  Contributed by
  nMustaki.

- Fixed Windows build due to URL change for `get-pip.py`.  Contributed by
  nMustaki.


# Version 2.2.0
#### 26 October 2015

- Python 3.5 support is now real, including automated builds for every commit.
  We now compensate for Python 3.5's new behavior of creating a dummy TestCase
  when failing to load a test target via a dotted name.  All tests now pass on
  Python 3.5 for the first time!  Lets keep it that way.  I'm crossing my
  fingers that this might fix #93, #96, or #98 (which I'll work on next if it
  didn't).  Fixes #99.

- When the summary output of a test case is longer than the terminal width and
  wraps to the next line, we now rewind the cursor back to the original spot
  when rewriting in the final color.  This means no more "duplicate" lines in
  verbose output with narrow terminal windows.  Fixes #84.


# Version 2.1.2
#### 20 October 2015

- Intercept and handle coverage 4.x's new exception that occurs if there is no
  coverage to report.


# Version 2.1.1
#### 19 October 2015

- Fixed the new `-u/--include-patterns` to actually break apart the
  comma-separated list into separate entries.  It was already working fine if
  you only included a single pattern.


# Version 2.1.0
#### 19 October 2015

- Removed official Python 3.4+ support on Windows, due to AppVeyor's
  aggravating fail-4-times-out-of-5 behavior which I can't replicate at all on
  real windows.  If someone wants to help find the problem so we can have
  consistent builds, I would be happy to restore official Python 3.4+ support
  on Windows.  In practice, everything functions fine on Windows as far as I
  can tell, but this will drift in the future without builds to let us know
  what breaks.

- Added `-u/--include-patterns` argument to pass through a list of include
  patterns to coverage. See the help docs for more info.

- Fixed a crash during handling a crash in loader code due to incorrect string
  formatting - contributed by jayvdb

- Green can now be run as a module with `python -m green` syntax - contributed
  by krisztianfekete, fixes #91

- Fixed the text describing the ordering of the screenshots - reported by
  robertlagrant


# Version 2.0.7
#### 18 September 2015

- Fixed help documentation for `-s/--processes` to account for changes made in
  the 2.0.0 overhaul.  Fixes #83.


# Version 2.0.6
#### 14 September 2015

- Green no longer follows symlinks during discovery, to avoid infinite
  discovering.


# Version 2.0.5
#### 14 September 2015

- Green no longer ignores config files when run as through django.  Fixes #79
  and #82.

- Green no longer crashes when run through django when no tests are present.

- Coverage output now appears before the summary, so that long coverage lists
  don't make it difficult to tell whether tests passed or not.

- Fixed a bug that would cause a crash if a python package with an invalid (and
  thus un-importable) name existed within the discovery scope.

- Updated the readme: swapped the features and screenshots section, swapped the
  positioning of the two screenshots.


# Version 2.0.4
#### 27 August 2015

- Fixed a bug that was causing crashes when subclassing Twisted's version of
  TestCase.


# Version 2.0.3
#### 23 August 2015

- When you use Python 2.7 and your failing test has a traceback that refers to
  a line that has unicode literals in it, green will now catch the resulting
  UnicodeDecodeError raised while trying to format the traceback and tell you the
  module it was trying to import and that it couldn't display the correct
  traceback due to the presence of a unicode literal. Resolves #77.


# Version 2.0.2
#### 20 August 2015

- Captured stdout and stderr is reported properly once again.  Regression in
  2.0.0.  Resolves issue #76.

- Better capturing and reporting of exceptions that escape the testing
  framework.

- Added screenshots to the readme file.  Resolves issue #78.

- Put the gitter badge inline with the other badges on the readme.

- Ignore build failures on the alpha OS X builders TravisCI suddenly (and
  finally) turned on for us.  They don't even have python installed yet...

- Use a consistent tagline for the project everywhere ("Green is a clean,
  colorful, fast python test runner.")



# Version 2.0.1
#### 30 July 2015

- Handled the case where a module could be discovered by directory searching by
  the main process but not by module name by the subprocess.  Instead of
  crashing the subprocess and hanging, we now handle it and report it as an
  importing problem.  One cause of this problem is forgetting your __init__.py
  Fixes issue #74.

- Improved some of our own unit tests to follow more best practices.  Fixes
  issue #62.;


# Version 2.0.0
#### 24 July 2015

- BREAKING CHANGE: Major overhaul of the multiprocessing system.  Tests always
  run in a separate worker process, even when only one process is specified.
  The default number of processes is now the number of logical processors
  detected instead of 1.  Entire modules are now run in the same worker process
  by default to avoid both the overhead of multiple processes loading the same
  module and the overhead of running module and class setUp/tearDown multiple
  times redundantly.  Classes or methods specified individually on the
  command-line will still be run in their own worker process.  A ton of credit
  for this feature needs to go to Sam Spilsbury, who put in considerable time
  and effort to actually code up the initial pull request.  Fixes 
  issues #68, #70.

- BREAKING CHANGE: Due the fact that no one uses it that I can tell and I don't
  want to maintain it, the `-m/--html` option has been removed.

- BREAKING CHANGE: `-o/--omit-patterns` now adds patterns to the default
  coverage omit list instead of replacing the default list.

- `-O/--clear-omit` was added to clear the default coverage omit list.

- `-k/--no-skip-report` was added to suppress the skip report if desired.

- Added a gitter chatroom link to the readme.

- Support for acquiring and releasing arbitrary resources via the
  `-i/--initializer` and `-z/--finalizer` options.  Use it to setup/teardown
  things that an individual worker process will need exclusive access to apart
  from the other worker processes.

- We're back at 100% self-test coverage again.  Yay!!!

- Twisted's skip functionality is caught and recorded as skips instead of
  failures, if your `TestCase` subclasses `twisted.trial.unittest.TestCase` and
  sets the class attribute `.skip` to `True`, or a test raises
  `twisted.trial.unittest.SkipTest`.

- Better handling of outside-of-test exceptions that occur inside worker
  processes.

- We now capture stderr that is emitted during tests and present it after tests
  have run, just like we do with stdout.

- Capturing stdout in worker processes more consistently works (no known bugs
  left).

- The headers for stdout and stderr are now yellow, for better color scheme
  consistency (and so they don't get confused with skip headers).

- Skip report headers now display the dotted test name in bold, just like other
  headers do.  We are so consistent!

- Fixed the skip report so it goes to the stream instead of stdout.

- Disabled the annoying "Coverage.py warning: No data was collected." message
  that started happening a lot, even though coverage was working just fine.

- Colors now work on AppVeyor builds, all hail the pretty colors!  (Ironically,
  they don't support Windows ansi colors, they wrote their own interpreters for
  posix-style color escape codes.)

- We now "close" the process pool instead of "terminating" it, which results in
  much better behavior in pypy and Windows, especially for things like tearDown
  stuff.


# Version 1.11.0
#### 18 June 2015

- Added support for pypy3.  Fiixes issue #63.

- Disabled the virtual-env aspect of test_versions when run in Travis-CI, which
  is already in a virtualenv.


# Version 1.10.0
#### 17 June 2015

- Virtualenv directories are now skipped during test discovery, so you can now
  use discovery on projects that contain one or more virtualenv directories
  inside of them.

- Green *always* runs tests in a separate process now, though by default it
  still (currently) defaults to only *one* separate process, to maximize
  compatibility with large suites that already assume tests are run sequentially.

- Green will now catch exceptions that the test framework doesn't handle and
  report them as test failures.  Specifically, if your test case subclasses
  `testtools.TestCase` from the popular `testtools` project, then `SystemExit`
  exceptions will escape the TestCase.  Green will catch these exceptions and
  report them as failures.  The one special-case is KeyboardInterrupt, which
  Green catches and interprets as a desire to terminate testing, and stops the
  test run.

- Changed the `-m/--html` help text to be a deprecation warning.  If you would
  like this feature to stay, please create an issue stating so at
  https://github.com/CleanCut/green/issues/new


# Version 1.9.4
#### 15 June 2015

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
#### 7 June 2015

- Switched to cyan instead of blue on Windows only.

- Stubbed in the beginnings of support for designating initialization to run in
  each process to obtain whatever resources might be needed by a single
  process (like its own database, for example).


# Version 1.9.2
#### 8 May 2015

- Fixed a regression that caused the `-a/--allow-stdout` cli option and
  corresponding config option to be ignored.  Fixes issue #58.


# Version 1.9.1
#### 13 April 2015

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
#### 8 April 2015

- BREAKING CHANGE: `--omit` was renamed to `--omit-patterns` for consistency
  with how other pattern-related options are named.

- BREAKING CHANGE: `--pattern` was renamed to `--file-pattern` for consistency
  with how other pattern-related options are named.

- Added `-n` / `--test-pattern` option to further refine which tests are
  actually run.  Thanks to Monty Hindman for a pull request that got this
  feature going.

- Tweaked Travis CI builds


# Version 1.8.1
#### 1 April 2015 (Not a joke!)

- Fixed issue where command-line arguments could not override config
arguments to set options back to default values.  Reported by Monty Hindman.
Issue #47.

- Converted this changelog file to markdown format.


# Version 1.8.0
#### 30 March 2015

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
#### 25 November 2014

- When run in completions mode (`green --completions`), import errors in
  potential modules are ignored, so that the completions list is still
  generated instead of producing crash output.


# Version 1.7.0
#### 21 September 2014

- Output sent to stdout is now captured and then presented along with the list
  of tracebacks.  This can be disabled with `-a/--allow-stdout`.  Issue #29.


# Version 1.6.0
#### 10 September 2014

- Added `-f/--failfast` to stop executing tests after the first error, failure,
  or unexpected successes.

- Simplified the usage line in the help output.


# Version 1.5.0
#### 31 August 2014

- You can press Ctrl-C once while tests are running to cleanly terminate the
  test run.

- Some internal refactoring.

- Python 3.3 is no longer supported on Windows.  It might work still--it's just
  not supported.

- Windows CI with AppVeyor is now passing.


# Version 1.4.4
#### 26 August 2014

- File handles are now explicitly closed in setup.py.  Contributed by Simeon
  Visser.


# Version 1.4.3
#### 26 August 2014

- Trying to import a module by name that raises an exception during import now
  manufactures a test that reports an ImportError instead of just silently
  ignoring the file.  Issue #31.


# Version 1.4.2
#### 14 August 2014

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
#### 30 July 2014

- We now use the fully-dotted test name at the start of each traceback in the
  error listing.  Issue #28.
- PyPy libraries are now omitted from coverage by default.
- More cleanup on internal tests.


# Version 1.4.0
#### 30 July 2014

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
#### 23 July 2014

- Fixed the new tests that failed if you ran them in-place on an installed
  version of green.  Forgot to check the build status before I did the last
  release!


# Version 1.3.0
#### 23 July 2014

- Bash-completion and ZSH-completion support for options and test targets.
  Issue #7.


# Version 1.2.1
#### 20 July 2014

- Multiline docstrings (with -vv or -vvv) on test methods are now handled
  correctly.  Initial whitespace is first stripped.  Then lines are combined
  into one space-separated string until the first blank line.  Issue #26.


# Version 1.2.0
#### 20 July 2014

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
#### 17 July 2014

- Configuration file support, originally contributed by Tom Barron - Issues
  #20, #23, #24


# Version 1.0.2
#### 6 July 2014

- Color works on Windows - Issues #18, #19

- Self-tests run against installed versions automatically - Issue #10

- Installation process is now tested automatically - Issue #9

- Switched to "branch-based development"

- Added an "example" directory with an example project with unit tests

- Added the CHANGELOG (this file)

- Improved the README.md file a lot based on feedback from reddit.


# Version 1.0.1
#### 23 June 2014

- Fixed MANIFEST so that installation didn't crash


# Version 1.0
#### 22 June 2014

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
