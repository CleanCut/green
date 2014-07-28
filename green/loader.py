from __future__ import unicode_literals
from collections import OrderedDict
from fnmatch import fnmatch
import functools
import glob
import importlib
import os
import re
import sys
import unittest
import traceback

from green.output import debug
from green.result import proto_test

python_file_pattern = re.compile(r'[_a-z]\w*\.py?$', re.IGNORECASE)


def toProtoTestList(suite_part, test_list=None):
    """
    Take a TestSuite and turn it into a list of ProtoTests.

    This function is recursive.  Pass it a suite, and it will re-call itself
    with smaller parts of the suite.
    """
    if test_list == None:
        test_list = []
    # Python's lousy handling of module import failures during loader discovery
    # makes this crazy special case necessary.  See _make_failed_import_test in
    # the source code for unittest.loader
    if suite_part.__class__.__name__ == 'ModuleImportFailure':
        exception_method = str(suite_part).split()[0]
        getattr(suite_part, exception_method)()
    # On to the real stuff
    if issubclass(type(suite_part), unittest.TestCase):
        test_list.append(proto_test(suite_part))
    else:
        for i in suite_part:
            toProtoTestList(i, test_list)
        return test_list


def getCompletions(target):
        # This option expects 0 or 1 targets
        if type(target) == list:
            target = target[0]
        if target == '.':
            target = ''

        # Discover tests and load them into a suite

        # First try the completion as-is.  It might be at a valid spot.
        test_suite = loadTargets(target)
        if not test_suite:
            # Next, try stripping to the previous '.'
            last_dot_idx = target.rfind('.')
            to_complete = None
            if last_dot_idx > 0:
                to_complete = target[:last_dot_idx]
            elif len(target):
                # Oops, there was no previous '.' -- try filesystem matches
                to_complete = glob.glob(target + '*')
            if not to_complete:
                to_complete = '.'
            test_suite = loadTargets(to_complete)

        # Reduce the suite to a list of relevant dotted names

        dotted_names = set()
        if test_suite:
            for dotted_name in [x.dotted_name for x in toProtoTestList(test_suite)]:
                if dotted_name.startswith(target):
                    dotted_names.add(dotted_name)
            # We have the fully dotted test names.  Now add the intermediate
            # completions.  bash and zsh will filter out the intermediats that
            # don't match.
            for dotted_name in list(dotted_names):
                while True:
                    idx = dotted_name.rfind('.')
                    if idx == -1:
                        break
                    dotted_name = dotted_name[:idx]
                    if dotted_name.startswith(target):
                        dotted_names.add(dotted_name)
                    else:
                        break
        return('\n'.join(sorted(list(dotted_names))))


def isPackage(file_path):
    """
    Determines whether or not a given path is a (sub)package or not.
    """
    return (os.path.isdir(file_path) and
            os.path.isfile(os.path.join(file_path, '__init__.py')))


def findDottedModuleAndParentDir(file_path):
    """
    I return a tuple (dotted_module, parent_dir) where dotted_module is the
    full dotted name of the module with respect to the package it is in, and
    parent_dir is the absolute path to the parent directory of the package.

    If the python file is not part of a package, I return (None, None).

    For for filepath /a/b/c/d.py where b is the package, ('b.c.d', '/a') would
    be returned.
    """
    if not os.path.isfile(file_path):
        raise ValueError("'{}' is not a file.".format(file_path))
    parent_dir = os.path.dirname(os.path.abspath(file_path))
    dotted_module = os.path.basename(file_path).replace('.py', '')
    while isPackage(parent_dir):
        dotted_module = os.path.basename(parent_dir) + '.' + dotted_module
        parent_dir = os.path.dirname(parent_dir)
    debug("Dotted module: {} -> {}".format(
        parent_dir, dotted_module), 2)
    return (dotted_module, parent_dir)


def loadFromTestCase(test_case_class):
    debug("Examining test case {}".format(test_case_class.__name__), 3)
    test_case_names = list(filter(
        lambda attrname: (attrname.startswith('test') and
                          callable(getattr(test_case_class, attrname))),
        dir(test_case_class)))
    debug("Test case names: {}".format(test_case_names))
    test_case_names.sort(
            key=functools.cmp_to_key(lambda x, y: (x > y) - (x < y)))
    if not test_case_names and hasattr(test_case_class, 'runTest'):
        test_case_names = ['runTest']
    return unittest.TestSuite(map(test_case_class, test_case_names))


def loadFromModule(module):
    debug("Examining module {} for test cases".format(module.__name__), 2)
    test_cases = []
    for item in dir(module):
        obj = getattr(module, item)
        if isinstance(obj, type) and issubclass(obj, unittest.case.TestCase):
            test_cases.append(loadFromTestCase(obj))
    return unittest.suite.TestSuite(test_cases)


def loadFromModuleFilename(filename):
    dotted_module, parent_dir = findDottedModuleAndParentDir(filename)
    # Adding the parent path of the module to the start of sys.path is
    # the closest we can get to an absolute import in Python that I can
    # find.
    sys.path.insert(0, parent_dir)
    try:
        __import__(dotted_module)
        loaded_module = sys.modules[dotted_module]
        debug("Imported {}".format(dotted_module), 2)
    except unittest.case.SkipTest as e:
        # TODO: #25 - Right now this mimics the behavior in unittest.  Lets
        # refactor it and simplify it after we make sure it works.
        # This is a cause of the traceback mangling I observed.
        reason = str(e)
        @unittest.case.skip(reason)
        def testSkipped(self):
            pass # pragma: no cover
        TestClass = type(
                str("ModuleSkipped"),
                (unittest.case.TestCase,),
                {filename: testSkipped})
        return unittest.suite.TestSuite((TestClass(filename),))
    except:
        # TODO: #25 - Right now this mimics the behavior in unittest.  Lets
        # refactor it and simplify it after we make sure it works.
        # This is a cause of the traceback mangling I observed.
        message = ('Failed to import {} computed from filename {}\n{}').format(
                       dotted_module, filename, traceback.format_exc())
        def testFailure(self):
            raise ImportError(message)
        TestClass = type(
                str("ModuleImportFailure"),
                (unittest.case.TestCase,),
                {filename: testFailure})
        return unittest.suite.TestSuite((TestClass(filename),))
    finally:
        # This gets called before return statements in except clauses
        # actually return.  Yay!
        sys.path.pop(0)

    # --- Find the tests inside the loaded module ---
    return loadFromModule(loaded_module)


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
            subdir_suite = discover(path, file_pattern)
            if subdir_suite:
                suite.addTest(subdir_suite)

        elif os.path.isfile(path):
            # Skip irrelevant files
            if not python_file_pattern.match(file_or_dir_name):
                continue
            if not fnmatch(file_or_dir_name, file_pattern):
                continue

            # Try loading the file as a module
            module_suite = loadFromModuleFilename(path)
            if module_suite:
                suite.addTest(module_suite)

    return ((suite.countTestCases() and suite) or None)


def loadTargets(targets, file_pattern='test*.py'):
    # If a string was passed in, put it into a list.
    if type(targets) != list:
        targets = [targets]

    # Make sure there are no duplicate entries, preserving order
    target_dict = OrderedDict()
    for target in targets:
        target_dict[target] = True
    targets = target_dict.keys()

    suites = []
    for target in targets:
        suite = loadTarget(target, file_pattern)
        if not suite:
            debug("Found 0 tests for target '{}'".format(target))
            continue
        suites.append(suite)
        num_tests = suite.countTestCases()
        debug("Found {} test{} for target '{}'".format(
            num_tests, '' if (num_tests == 1) else 's', target))

    if suites:
        return unittest.TestSuite(suites)
    else:
        return None


def loadTarget(target, file_pattern='test*.py'):
    """
    """
    debug("Attempting to load target '{}' with file_pattern '{}'".format(
        target, file_pattern))
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
        except (ImportError, KeyError):
            pkg_in_path_dir = None

    # => DISCOVER DIRS
    tests = None
    for candidate in [bare_dir, dot_dir, pkg_in_path_dir]:
        if (candidate == None) or (not os.path.isdir(candidate)):
            continue
        tests = discover(candidate)
        if tests and tests.countTestCases():
            debug("Load method: DISCOVER - {}".format(candidate))
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
            debug("Load method: DOTTED OBJECT - {}".format(target))
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
            slashed_path = target.replace('.py', '').replace(os.sep, '.')
            tests = loader.loadTestsFromName(slashed_path)
        except: # Any exception could occur here
            pass
        if need_cleanup:
            sys.path.remove(cwd)
        if tests and tests.countTestCases():
            debug("Load method: FILE - {}".format(candidate))
            return tests

    return None
