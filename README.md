Green
=====

Clean, colorful test runner for Python
--------------------------------------
[![Version](http://img.shields.io/pypi/v/green.svg?style=flat)](https://pypi.python.org/pypi/green)

Green is a clean, colorful test runner for Python unit tests.  Compare it to
nose, nose2, and trial.

Basic Usage
===========

See some (hopefully) passing tests:

    green -v green.tests

See all the different kinds of failures, errors, etc. that could occur:

    green -v green.examples

To use Green with existing Python unit tests, just run `green` in the home
directory of your project.  (To make it easier on developers with multiple
versions of Python installed, we also install greenX and green-X.Y, where X is
the major version number of Python [2 or 3] and Y is the minor version number.)

For more advanced usage, see `green --help`

Screenshots
===========

Okay, so I haven't figured out how to get screenshots into the README yet, but
you can take a look at some example output by running `green -vv
green.examples`

Installation
============

For most versions of python 2.x you should use `pip`.  You may have to preface
this command with `sudo` if you do not have root permissions.

    pip install green

For more recent versions of Python 3, the command is usually nearly the same
(you still may have to preface the command with `sudo`).

    pip3 install green


Upgrading
=========

Just add the `--upgrade` option to what you used above.  For example:

    pip3 install --upgrade green


Uninstalling
============

Replace `install` with `uninstall` in the command from the Installation section
above.
