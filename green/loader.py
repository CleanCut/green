from __future__ import unicode_literals
from collections import OrderedDict
import importlib
import logging
import os
import sys
import unittest


def getTests(targets):
    # If a string was passed in, put it into a list.
    if type(targets) != list:
        targets = [targets]

    # Make sure there are no duplicate entries, preserving order
    target_dict = OrderedDict()
    for target in targets:
        target_dict[target] = True
    targets = target_dict.keys()

    # Get the tests
    tests = None
    for target in targets:
        more_tests = getTest(target)
        if not more_tests:
            logging.debug("Found 0 tests for target '{}'".format(target))
            continue
        num_tests = more_tests.countTestCases()
        logging.debug("Found {} test{} for target '{}'".format(
            num_tests, '' if (num_tests == 1) else 's', target))
        if not tests:
            tests = more_tests
        else:
            tests.addTests(more_tests)

    return tests


def makeDottedName(base_dir, file_path):
    """
    I convert a file_path into a dotted name based on a base_dir.

    For example:

    makeDotted('/start/dir/', '/start/dir/pkg/module.py')

    ...would likely return 'pkg.module'

    If the file does not have a proper Python extension, then AttributeError
    is raised.
    """
    dotted_name = file_path.replace(base_dir, '').lstrip(os.sep)
    found = False
    for suffix in ['.py', '.pyc', '.pyo']:
        if dotted_name.endswith(suffix):
            found = True
            dotted_name = dotted_name[:len(dotted_name)-len(suffix)]
    if not found:
        raise AttributeError("No valid python extension found")
    dotted_name = dotted_name.replace(os.sep, '.')
    return dotted_name


def isPkg(path):
    return (os.path.isdir(path) and
            (
                os.path.isfile(os.path.join(path, '__init__.py'))
                or os.path.isfile(os.path.join(path, '__init__.pyc'))
                or os.path.isfile(os.path.join(path, '__init__.pyo'))
            ))


def discoverDottedNames(start_dir, pkg_dir=None):
    """
    I discover all the valid dotted names in a directory.

    start_dir is used when the function calls itself recursively
    """
    if not pkg_dir:
        if isPkg(start_dir):
            pkg_dir = start_dir
            while isPkg(os.path.dirname(pkg_dir)):
                pkg_dir = os.path.dirname(pkg_dir)
    dottedNames = OrderedDict()
    paths = sorted(os.listdir(start_dir))
    for path in paths:
        path = os.path.join(start_dir, path)
        if os.path.isfile(path):
            try:
                dottedNames[makeDottedName(path, pkg_dir)] = True
            except AttributeError:
                pass
        elif os.path.isdir(path) and pkg_dir:
            if isPkg(path):
                for dottedName in discoverDottedNames(path, pkg_dir):
                    dottedNames[dottedName] = True
    return list(dottedNames.keys())


def discover():
    pass



def load(target='.', file_pattern='test*.py'):
    """
    """
    loader = unittest.TestLoader()

    # For a test loader, we want to always the current working directory to be
    # the first item in sys.path, just like when a python interpreter is loaded
    # interactively.  See also
    # https://docs.python.org/3.4/library/sys.html#sys.path
    if sys.path[0] != '':
        sys.path.insert(0, '')

    # DIRECTORY VARIATIONS - These will discover all tests in a directory
    # structure, whether or not they are accessible by the root package.

    # some/real/dir
    bare_dir = target
    # some.real.dir
    if ('.' in target) and (len(target) > 1):
        dot_dir  = target[0] + target[1:].replace('.', os.sep)
    else:
        dot_dir = None
    # pyzmq.tests  (Package (=dir) in PYTHONPATH, including installed ones)
    pkg_in_path_dir = None
    if target and (target[0] != '.'):
        try:
            filename = importlib.import_module(target).__file__
            if '__init__.py' in filename:
                pkg_in_path_dir = os.path.dirname(filename)
        except ImportError:
            pkg_in_path_dir = None

    # => DISCOVER DIRS
    tests = None
    for candidate in [bare_dir, dot_dir, pkg_in_path_dir]:
        if (candidate == None) or (not os.path.isdir(candidate)):
            continue
        tests = discover(candidate)
        if tests and tests.countTestCases():
            logging.debug("Load method: DISCOVER - {}".format(candidate))
            return tests


    # DOTTED OBJECT - These will discover a specific object if it is
    # globally importable or importable from the current working directory.
    # Examples: pkg, pkg.module, pkg.module.class, pkg.module.class.func
    tests = None
    if target and (target[0] != '.'): # We don't handle relative dot objects
        try:
            tests = loader.loadTestsFromName(target)
        except (ImportError, AttributeError):
            pass
        if tests and tests.countTestCases():
            logging.debug("Load method: DOTTED OBJECT - {}".format(target))
            return tests


    # FILE VARIATIONS - These will import a specific file and any tests
    # accessible from its scope.

    # some/file.py
    bare_file = target
    # some/file
    pyless_file = target + '.py'
    for candidate in [bare_file, pyless_file]:
        if (candidate == None) or (not os.path.isfile(candidate)):
            continue
        need_cleanup = False
        cwd = os.getcwd()
        if cwd != sys.path[0]:
            need_cleanup = True
            sys.path.insert(0, cwd)
        try:
            # In OS X, /var is a symlink to /private/var, and for some reason
            # this works better if we use the /var symlink
            slashed_path = target.replace('.py', '').replace(os.sep, '.')
            tests = loader.loadTestsFromName(slashed_path)
        except: # Any exception could occur here
            pass
        if need_cleanup:
            sys.path.remove(cwd)
        if tests and tests.countTestCases():
            logging.debug("Load method: FILE - {}".format(candidate))
            return tests

    return None

def getTest(target):
    loader = unittest.TestLoader()

    # For a test loader, we want to always the current working directory to be
    # the first item in sys.path, just like when a python interpreter is loaded
    # interactively.  See also
    # https://docs.python.org/3.4/library/sys.html#sys.path
    if sys.path[0] != '':
        sys.path.insert(0, '')

    # DIRECTORY VARIATIONS - These will discover all tests in a directory
    # structure, whether or not they are accessible by the root package.

    # some/real/dir
    bare_dir = target
    # some.real.dir
    if ('.' in target) and (len(target) > 1):
        dot_dir  = target[0] + target[1:].replace('.', os.sep)
    else:
        dot_dir = None
    # pyzmq.tests  (Package (=dir) in PYTHONPATH, including installed ones)
    pkg_in_path_dir = None
    if target and (target[0] != '.'):
        try:
            filename = importlib.import_module(target).__file__
            if '__init__.py' in filename:
                pkg_in_path_dir = os.path.dirname(filename)
        except ImportError:
            pkg_in_path_dir = None

    # => DISCOVER DIRS
    tests = None
    for candidate in [bare_dir, dot_dir, pkg_in_path_dir]:
        if (candidate == None) or (not os.path.isdir(candidate)):
            continue
        # TestLoader.discover() rudely alters the path.  Not usually a big deal
        # for people who call it only once, but it wreaks havoc on our internal
        # unittests! We'll have to restore it ourselves.
        saved_sys_path = sys.path[:]
        tests = loader.discover(candidate)
        sys.path = saved_sys_path
        if tests and tests.countTestCases():
            logging.debug("Load method: DISCOVER - {}".format(candidate))
            return tests


    # DOTTED OBJECT - These will discover a specific object if it is
    # globally importable or importable from the current working directory.
    # Examples: pkg, pkg.module, pkg.module.class, pkg.module.class.func
    tests = None
    if target and (target[0] != '.'): # We don't handle relative dot objects
        try:
            tests = loader.loadTestsFromName(target)
        except (ImportError, AttributeError):
            pass
        if tests and tests.countTestCases():
            logging.debug("Load method: DOTTED OBJECT - {}".format(target))
            return tests


    # FILE VARIATIONS - These will import a specific file and any tests
    # accessible from its scope.

    # some/file.py
    bare_file = target
    # some/file
    pyless_file = target + '.py'
    for candidate in [bare_file, pyless_file]:
        if (candidate == None) or (not os.path.isfile(candidate)):
            continue
        need_cleanup = False
        cwd = os.getcwd()
        if cwd != sys.path[0]:
            need_cleanup = True
            sys.path.insert(0, cwd)
        try:
            # In OS X, /var is a symlink to /private/var, and for some reason
            # this works better if we use the /var symlink
            slashed_path = target.replace('.py', '').replace(os.sep, '.')
            tests = loader.loadTestsFromName(slashed_path)
        except: # Any exception could occur here
            pass
        if need_cleanup:
            sys.path.remove(cwd)
        if tests and tests.countTestCases():
            logging.debug("Load method: FILE - {}".format(candidate))
            return tests

    return None
