from __future__ import unicode_literals
from collections import OrderedDict
from fnmatch import fnmatch
import importlib
import logging
import os
import re
import sys
import unittest
import traceback


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


def isPackage(file_path):
    return (os.path.isdir(file_path) and
            os.path.isfile(os.path.join(file_path, '__init__.py')))


python_file_pattern = re.compile(r'[_a-z]\w*\.py?$', re.IGNORECASE)
def findDottedModuleAndParentDir(file_path):
    """
    I return a tuple (dotted_module, parent_dir) where dotted_module is the
    full dotted name of the module with respect to the package it is in, and
    parent_dir is the absolute path to the parent directory of the package.

    If the python file is not part of a package, I return (None, None).

    For for filepath /a/b/c/d.py where b is the package, ('b.c.d', '/a') would
    be returned.
    """
    parent_dir = os.path.dirname(os.path.abspath(file_path))
    dotted_module = os.path.basename(file_path).replace('.py', '')
    while isPackage(parent_dir):
        dotted_module = os.path.basename(parent_dir) + '.' + dotted_module
        parent_dir = os.path.dirname(parent_dir)
    return (dotted_module, parent_dir)


def discover(current_path, file_pattern='test*.py'):
    """
    I take a path to a directory and discover all the tests inside files
    matching file_pattern.

    If path is not a readable directory, I raise an ImportError.

    If I don't find anything, I return None.  Otherwise I return a
    unittest.TestSuite -- but that may change someday.
    """
    current_abspath = os.path.abspath(current_path)
    if not os.path.isdir(current_abspath):
        raise ImportError(
                "'%s' is not a directory".format(str(current_path)))
    suite = unittest.suite.TestSuite()
    for file_or_dir_name in sorted(os.listdir(current_abspath)):
        path = os.path.join(current_abspath, file_or_dir_name)
        # Recurse into directories
        if os.path.isdir(path):
            sub_suite = discover(path, file_pattern)
            if sub_suite:
                suite.addTest(sub_suite)

        elif os.path.isfile(current_abspath):
            # Skip irrelevant files
            if not python_file_pattern.match(file_or_dir_name):
                continue
            if not fnmatch(file_or_dir_name, file_pattern):
                continue

            # --- Try loading the file as a module ---
            dotted_module, parent_dir = findDottedModuleAndParentDir(
                    file_or_dir_name)
            # Adding the parent path of the module to the start of sys.path is
            # the closest we can get to an absolute import in Python that I can
            # find.
            sys.path.insert(0, parent_dir)
            try:
                __import__(dotted_module)
                loaded_module = sys.modules[dotted_module]
            except unittest.case.SkipTest as e:
                # TODO: Right now this mimics the behavior in unittest.  Lets
                # refactor it and simplify it after we make sure it works.
                reason = str(e)
                @unittest.case.skip(reason)
                def testSkipped(self):
                    pass
                TestClass = type(
                        "ModuleSkipped",
                        (unittest.case.TestCase,),
                        {file_or_dir_name: testSkipped})
                return unittest.suite.TestSuite((TestClass(file_or_dir_name),))
            except:
                # TODO: Right now this mimics the behavior in unittest.  Lets
                # refactor it and simplify it after we make sure it works.
                message = 'Failed to import test module: {}\n{}'.format(
                        file_or_dir_name, traceback.format_exc())
                def testFailure(self):
                    raise ImportError(message)
                TestClass = type(
                        "ModuleImportFailure",
                        (unittest.case.TestCase,),
                        {file_or_dir_name: testFailure})
                return unittest.suite.TestSuite((TestClass(file_or_dir_name),))
            finally:
                # This gets called before return statements in except clauses
                # actually return.  Yay!
                sys.path.pop(0)

            # --- Find the tests inside the loaded module ---
            # XXX



    if suite.countTestCases():
        return suite
    else:
        return None








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
