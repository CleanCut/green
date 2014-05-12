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
-----------

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
