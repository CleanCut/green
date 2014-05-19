Green
=====

Clean, colorful test runner for Python
--------------------------------------
[![Version](https://img.shields.io/pypi/v/green.svg?style=flat)](https://pypi.python.org/pypi/green)
[![Build Status](https://img.shields.io/travis/CleanCut/green.svg?style=flat)](https://travis-ci.org/CleanCut/green)
[![Coverage Status](https://coveralls.io/repos/CleanCut/green/badge.png?branch=master)](https://coveralls.io/r/CleanCut/green?branch=master)
[![Coverage Status](https://img.shields.io/coveralls/CleanCut/green.svg)](https://coveralls.io/r/CleanCut/green?branch=master)

Green is a clean, colorful test runner for Python unit tests.  Compare it to
nose or trial.

Green grew out of a desire to see pretty colors.  Really!  A big part of the
whole the **Red/Green/Refactor** process in test-driven-development is
_actually getting to see red and green output_.  Most python unit testing
actually goes **Gray/Gray/Refactor** (at least on my terminal, which is gray
text on black background).  That's a shame.  Even TV is in color these days.
Why not terminal output?  Even worse, the default output for most test runners
is cluttered, hard-to-read, redundant, and the dang statuses are not aligned
vertically!  Green fixes all that.

### Features ###

- Colored terminal output
- Aligned status indicators
- Test discovery
- Flexible test target specification
- No new objects to learn -- just use normal `unittest` classes.
- HTML output
- Four verbosity levels
- Built-in, optional, integration with
  [coverage](http://nedbatchelder.com/code/coverage/)
- Supports Python 2.7, 3.3, 3.4, and [PyPy](http://pypy.org)
- Completely supports OS X and Linux, most likely BSDs (and maybe Windows,
  someone want to try it and let me know?)

### Wish List ###

- Parallel test-running (multiprocessing)

Basic Usage
-----------

The simplest way is to just run `green` directory of your project.  (For
convenience, you can also use `greenX` or `greenX.Y`, where `X` and `Y` are the
major and minor version number of your Python installation.)

By default, Green mimics the verbosity levels of vanilla unittest or nose,
meaning that output is mostly just dots.  For Green we recommend adding more
verbosity by using the `-v` or `-vv` options.

To run Green's own internal unit tests (which are hopefully all passing):

    green -v green

To see all examples of all the failures, errors, etc. that could occur:

    green -v green.examples


Advanced Usage
--------------

Please see `green --help`


Install
-------

Replace `pip3` with your version of pip if necessary.  You may need to prepend
this command with `sudo` or run it as root if your normal user cannot write to
the local Python package directory.

    pip3 install green


Upgrade
-------

    pip3 install --upgrade green

Wait...what do I have installed?

    green --version


Uninstall
---------

    pip3 uninstall green
