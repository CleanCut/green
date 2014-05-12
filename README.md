Green
=====

Clean, colorful test runner for Python
--------------------------------------
[![Version](http://img.shields.io/pypi/v/green.svg?style=flat)](https://pypi.python.org/pypi/green)

Green is a clean, colorful test runner for Python unit tests.  Compare it to
nose or trial.

Green currently supports Python 2.7.x and 3.4.x.  Python 2.6 and older will
never be supported.  Python 3.0-3.3 may be supported depending on difficulty
and user requests.


Basic Usage
===========

To use Green with existing Python unit tests, just run `green` in the home
directory of your project.  (To make it easier on developers with multiple
versions of Python installed, we also install `greenX` and `green-X.Y`, where
`X` is the major version number of Python and `Y` is the minor version number.)

By default, Green mimics the verbosity levels of vanilla unittest or nose,
meaning that output is mostly just dots.  For Green we recommend adding more
verbosity by using the `-v` or `-vv` options.

To run Green's own internal unit tests (which are hopefully all passing):

    green -v green

To see all examples of all the failures, errors, etc. that could occur:

    green -v green.examples


Advanced Usage
==============

Please see `green --help`


Installation
============

For recent versions of Python 3, the command is usually (you may have to
preface the command with `sudo`):

    pip3 install green


Upgrading
=========

Just add the `--upgrade` option to what you used above.  For example:

    pip3 install --upgrade green


Uninstalling
============

Replace `install` with `uninstall`:

    pip3 uninstall green
