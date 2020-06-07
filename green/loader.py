from __future__ import unicode_literals
from collections import OrderedDict
from doctest import DocTestCase, DocTestSuite
from fnmatch import fnmatch
import functools
import glob
import importlib
import operator
import os
import re
import sys
import unittest
import traceback

from green.output import debug
from green.result import proto_test
from green.suite import GreenTestSuite

python_file_pattern = re.compile(r"^[_a-z]\w*?\.py$", re.IGNORECASE)
python_dir_pattern = re.compile(r"^[_a-z]\w*?$", re.IGNORECASE)



class GreenTestLoader(unittest.TestLoader):

    suiteClass = GreenTestSuite

    def loadTestsFromTestCase(self, testCaseClass):
        debug("Examining test case {}".format(testCaseClass.__name__), 3)

        def filter_test_methods(attrname):
            return (
                attrname.startswith(self.testMethodPrefix)
                and callable(getattr(testCaseClass, attrname))
                and not isTestCaseDisabled(testCaseClass, attrname)
            )

        test_case_names = list(filter(filter_test_methods, dir(testCaseClass)))
        debug("Test case names: {}".format(test_case_names))

        # Use default unittest.TestSuite sorting method if not overriden
        test_case_names.sort(key=functools.cmp_to_key(self.sortTestMethodsUsing))

        if not test_case_names and hasattr(testCaseClass, "runTest"):
            test_case_names = ["runTest"]
        return flattenTestSuite(map(testCaseClass, test_case_names))

    def loadFromModuleFilename(self, filename):
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
                pass  # pragma: no cover

            TestClass = type(
                str("ModuleSkipped"), (unittest.case.TestCase,), {filename: testSkipped}
            )
            return self.suiteClass((TestClass(filename),))
        except:
            # TODO: #25 - Right now this mimics the behavior in unittest.  Lets
            # refactor it and simplify it after we make sure it works.
            # This is a cause of the traceback mangling I observed.
            message = ("Failed to import {} computed from filename {}\n{}").format(
                dotted_module, filename, traceback.format_exc()
            )

            def testFailure(self):
                raise ImportError(message)

            TestClass = type(
                str("ModuleImportFailure"),
                (unittest.case.TestCase,),
                {filename: testFailure},
            )
            return self.suiteClass((TestClass(filename),))
        finally:
            # This gets called before return statements in except clauses
            # actually return. Yay!
            sys.path.pop(0)

        # --- Find the tests inside the loaded module ---
        return self.loadTestsFromModule(loaded_module)

    if sys.version_info >= (3, 5):  # pragma: no cover

        def loadTestsFromModule(self, module, pattern=None):
            tests = super(GreenTestLoader, self).loadTestsFromModule(
                module, pattern=pattern
            )
            return flattenTestSuite(tests, module)

    else:  # pragma: no cover

        def loadTestsFromModule(self, module):
            tests = super(GreenTestLoader, self).loadTestsFromModule(module)
            return flattenTestSuite(tests, module)

    def loadTestsFromName(self, name, module=None):
        tests = super(GreenTestLoader, self).loadTestsFromName(name, module)
        return flattenTestSuite(tests, module)

    def discover(self, current_path, file_pattern="test*.py", top_level_dir=None):
        """
        I take a path to a directory and discover all the tests inside files
        matching file_pattern.

        If path is not a readable directory, I raise an ImportError.

        If I don't find anything, I return None.  Otherwise I return a
        GreenTestSuite
        """
        current_abspath = os.path.abspath(current_path)
        if not os.path.isdir(current_abspath):
            raise ImportError("'{}' is not a directory".format(str(current_path)))
        suite = GreenTestSuite()
        try:
            for file_or_dir_name in sorted(os.listdir(current_abspath)):
                path = os.path.join(current_abspath, file_or_dir_name)
                # Recurse into directories, attempting to skip virtual environments
                bin_activate = os.path.join(path, "bin", "activate")
                if os.path.isdir(path) and not os.path.isfile(bin_activate):
                    # Don't follow symlinks
                    if os.path.islink(path):
                        continue
                    # Don't recurse into directories that couldn't be a package name
                    if not python_dir_pattern.match(file_or_dir_name):
                        continue

                    subdir_suite = self.discover(
                        path,
                        file_pattern=file_pattern,
                        top_level_dir=top_level_dir or current_path,
                    )

                    if subdir_suite:
                        suite.addTest(subdir_suite)

                elif os.path.isfile(path):
                    # Skip irrelevant files
                    if not python_file_pattern.match(file_or_dir_name):
                        continue
                    if not fnmatch(file_or_dir_name, file_pattern):
                        continue

                    # Try loading the file as a module
                    module_suite = self.loadFromModuleFilename(path)
                    if module_suite:
                        suite.addTest(module_suite)
        except OSError:
            debug("WARNING: Test discovery failed at path {}".format(current_path))

        return flattenTestSuite(suite) if suite.countTestCases() else None

    def loadTargets(self, targets, file_pattern="test*.py"):
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
            suite = self.loadTarget(target, file_pattern)
            if not suite:
                debug("Found 0 tests for target '{}'".format(target))
                continue
            suites.append(suite)
            num_tests = suite.countTestCases()
            debug(
                "Found {} test{} for target '{}'".format(
                    num_tests, "" if (num_tests == 1) else "s", target
                )
            )

        return flattenTestSuite(suites) if suites else None

    def loadTarget(self, target, file_pattern="test*.py"):
        """
        """
        debug(
            "Attempting to load target '{}' with file_pattern '{}'".format(
                target, file_pattern
            )
        )

        # For a test loader, we want to always the current working directory to
        # be the first item in sys.path, just like when a python interpreter is
        # loaded interactively. See also
        # https://docs.python.org/3.8/library/sys.html#sys.path
        if sys.path[0] != "":
            sys.path.insert(0, "")

        # DIRECTORY VARIATIONS - These will discover all tests in a directory
        # structure, whether or not they are accessible by the root package.

        # some/real/dir
        bare_dir = target
        # some.real.dir
        if ("." in target) and (len(target) > 1):
            dot_dir = target[0] + target[1:].replace(".", os.sep)
        else:
            dot_dir = None
        # pyzmq.tests  (Package (=dir) in PYTHONPATH, including installed ones)
        pkg_in_path_dir = None
        if target and (target[0] != "."):
            try:
                filename = importlib.import_module(target).__file__
                if "__init__.py" in filename:
                    pkg_in_path_dir = os.path.dirname(filename)
            except:
                pkg_in_path_dir = None

        # => DISCOVER DIRS
        tests = None
        for candidate in [bare_dir, dot_dir, pkg_in_path_dir]:
            if (candidate is None) or (not os.path.isdir(candidate)):
                continue
            tests = self.discover(candidate, file_pattern=file_pattern)
            if tests and tests.countTestCases():
                debug("Load method: DISCOVER - {}".format(candidate))
                return flattenTestSuite(tests)

        # DOTTED OBJECT - These will discover a specific object if it is
        # globally importable or importable from the current working directory.
        # Examples: pkg, pkg.module, pkg.module.class, pkg.module.class.func
        tests = None
        if target and (target[0] != "."):  # We don't handle relative
            try:  # dot objects
                tests = self.suiteClass(self.loadTestsFromName(target))
                for index, test in enumerate(tests):
                    if test.__class__.__name__ == "_FailedTest":  # pragma: no cover
                        del tests._tests[index]

            except Exception as e:
                debug("IGNORED exception: {}".format(e))
            if tests and tests.countTestCases():
                debug("Load method: DOTTED OBJECT - {}".format(target))
                return flattenTestSuite(tests)

        # FILE VARIATIONS - These will import a specific file and any tests
        # accessible from its scope.

        # some/file.py
        bare_file = target
        # some/file
        pyless_file = target + ".py"
        for candidate in [bare_file, pyless_file]:
            if (candidate is None) or (not os.path.isfile(candidate)):
                continue
            need_cleanup = False
            cwd = os.getcwd()
            if cwd != sys.path[0]:
                need_cleanup = True
                sys.path.insert(0, cwd)
            try:
                dotted_path = target.replace(".py", "").replace(os.sep, ".")
                tests = self.suiteClass(self.loadTestsFromName(dotted_path))
            except:  # Any exception could occur here
                # TODO: #25 - Right now this mimics the behavior in unittest.
                # Lets refactor it and simplify it after we make sure it works.
                # This is a cause of the traceback mangling I observed.
                try:
                    message = ('Failed to import "{}":\n{}').format(
                        dotted_path, traceback.format_exc()
                    )
                # If the line that caused the exception has unicode literals in it
                # anywhere, then python 2.7 will crash on traceback.format_exc().
                # Python 3 is ok.
                except UnicodeDecodeError:  # pragma: no cover
                    message = (
                        'Failed to import "{}", and the import traceback has a'
                        " unicode decode error, so I can't display "
                        "it.".format(dotted_path)
                    )

                def testFailure(self):
                    raise ImportError(message)  # pragma: no cover

                TestClass = type(
                    str("ModuleImportFailure"),
                    (unittest.case.TestCase,),
                    {dotted_path: testFailure},
                )
                return self.suiteClass((TestClass(dotted_path),))
            if need_cleanup:
                sys.path.remove(cwd)
            if tests and tests.countTestCases():
                debug("Load method: FILE - {}".format(candidate))
                return tests

        return None


def toProtoTestList(suite, test_list=None, doing_completions=False):
    """
    Take a test suite and turn it into a list of ProtoTests.

    This function is recursive.  Pass it a suite, and it will re-call itself
    with smaller parts of the suite.
    """
    if test_list is None:
        test_list = []
    # Python's lousy handling of module import failures during loader
    # discovery makes this crazy special case necessary.  See
    # _make_failed_import_test in the source code for unittest.loader
    if suite.__class__.__name__ == "ModuleImportFailure":
        if doing_completions:
            return test_list
        exception_method = str(suite).split("(")[0]
        getattr(suite, exception_method.strip())()
    # On to the real stuff
    if isinstance(suite, unittest.TestCase):
        # Skip actual blank TestCase objects that twisted inserts
        if str(type(suite)) != "<class 'twisted.trial.unittest.TestCase'>":
            test_list.append(proto_test(suite))
    else:
        for i in suite:
            toProtoTestList(i, test_list, doing_completions)
    return test_list


def toParallelTargets(suite, targets):
    """
    Produce a list of targets which should be tested in parallel.

    For the most part this will be a list of test modules.  The exception is
    when a dotted name representing something more granular than a module
    was input (like an individal test case or test method)
    """
    targets = filter(lambda x: x != ".", targets)
    # First, convert the suite to a proto test list - proto tests nicely
    # parse things like the fully dotted name of the test and the
    # finest-grained module it belongs to, which simplifies our job.
    proto_test_list = toProtoTestList(suite)
    # Extract a list of the modules that all of the discovered tests are in
    modules = set([x.module for x in proto_test_list])
    # Get the list of user-specified targets that are NOT modules
    non_module_targets = []
    for target in targets:
        if not list(filter(None, [target in x for x in modules])):
            non_module_targets.append(target)
    # Main loop -- iterating through all loaded test methods
    parallel_targets = []
    for test in proto_test_list:
        found = False
        for target in non_module_targets:
            # target is a dotted name of either a test case or test method
            # here test.dotted_name is always a dotted name of a method
            if target in test.dotted_name:
                if target not in parallel_targets:
                    # Explicitly specified targets get their own entry to
                    # run parallel to everything else
                    parallel_targets.append(target)
                found = True
                break
        if found:
            continue
        # This test does not appear to be part of a specified target, so
        # its entire module must have been discovered, so just add the
        # whole module to the list if we haven't already.
        if test.module not in parallel_targets:
            parallel_targets.append(test.module)

    return parallel_targets


def getCompletions(target):
    # This option expects 0 or 1 targets
    if type(target) == list:
        target = target[0]
    if target == ".":
        target = ""

    # Discover tests and load them into a suite

    # First try the completion as-is.  It might be at a valid spot.
    loader = GreenTestLoader()
    test_suite = loader.loadTargets(target)
    if not test_suite:
        # Next, try stripping to the previous '.'
        last_dot_idx = target.rfind(".")
        to_complete = None
        if last_dot_idx > 0:
            to_complete = target[:last_dot_idx]
        elif len(target):
            # Oops, there was no previous '.' -- try filesystem matches
            to_complete = glob.glob(target + "*")
        if not to_complete:
            to_complete = "."
        test_suite = loader.loadTargets(to_complete)

    # Reduce the suite to a list of relevant dotted names
    dotted_names = set()
    if test_suite:
        for dotted_name in map(
            operator.attrgetter("dotted_name"), toProtoTestList(test_suite, None, True)
        ):
            if dotted_name.startswith(target):
                dotted_names.add(dotted_name)
        # We have the fully dotted test names.  Now add the intermediate
        # completions.  bash and zsh will filter out the intermediates
        # that don't match.
        for dotted_name in list(dotted_names):
            while True:
                idx = dotted_name.rfind(".")
                if idx == -1:
                    break
                dotted_name = dotted_name[:idx]
                if dotted_name.startswith(target):
                    dotted_names.add(dotted_name)
                else:
                    break
    return "\n".join(sorted(list(dotted_names)))


def isPackage(file_path):
    """
    Determine whether or not a given path is a (sub)package or not.
    """
    return os.path.isdir(file_path) and os.path.isfile(
        os.path.join(file_path, "__init__.py")
    )


def findDottedModuleAndParentDir(file_path):
    """
    I return a tuple (dotted_module, parent_dir) where dotted_module is the
    full dotted name of the module with respect to the package it is in, and
    parent_dir is the absolute path to the parent directory of the package.

    If the python file is not part of a package, I return (None, None).

    For for filepath /a/b/c/d.py where b is the package, ('b.c.d', '/a')
    would be returned.
    """
    if not os.path.isfile(file_path):
        raise ValueError("'{}' is not a file.".format(file_path))
    parent_dir = os.path.dirname(os.path.abspath(file_path))
    dotted_module = os.path.basename(file_path).replace(".py", "")
    while isPackage(parent_dir):
        dotted_module = os.path.basename(parent_dir) + "." + dotted_module
        parent_dir = os.path.dirname(parent_dir)
    debug("Dotted module: {} -> {}".format(parent_dir, dotted_module), 2)
    return (dotted_module, parent_dir)


def isTestCaseDisabled(test_case_class, method_name):
    """
    I check to see if a method on a TestCase has been disabled via nose's
    convention for disabling a TestCase.  This makes it so that users can
    mix nose's parameterized tests with green as a runner.
    """
    test_method = getattr(test_case_class, method_name)
    return getattr(test_method, "__test__", "not nose") is False


def flattenTestSuite(test_suite, module=None):
    # Look for a `doctest_modules` list and attempt to add doctest tests to the
    # suite of tests that we are about to flatten.
    # todo: rename this function to something more appropriate.
    suites = [test_suite]
    doctest_modules = getattr(module, "doctest_modules", ())
    for doctest_module in doctest_modules:
        suite = DocTestSuite(doctest_module)
        suite.injected_module = module.__name__
        suites.append(suite)

    # Now extract all tests from the suite heirarchies and flatten them into a
    # single suite with all tests.
    tests = []
    for suite in suites:
        injected_module = None
        if getattr(suite, "injected_module", None):
            injected_module = suite.injected_module
        for test in suite:
            if injected_module:
                # For doctests, inject the test module name so we can later
                # grab it and use it to group the doctest output along with the
                # test module which specified it should be run.
                test.__module__ = injected_module
            if isinstance(test, unittest.BaseTestSuite):
                tests.extend(flattenTestSuite(test))
            else:
                tests.append(test)
    return GreenTestLoader.suiteClass(tests)
