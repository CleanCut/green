from __future__ import annotations

import pathlib
from doctest import DocTestSuite
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
from typing import Iterable, Type, TYPE_CHECKING, Union

from green.output import debug
from green import result
from green.suite import GreenTestSuite

if TYPE_CHECKING:
    from types import ModuleType
    from unittest import TestSuite, TestCase
    from doctest import _DocTestSuite

    FlattenableTests = Union[TestSuite, _DocTestSuite, GreenTestSuite]

python_file_pattern = re.compile(r"^[_a-z]\w*?\.py$", re.IGNORECASE)
python_dir_pattern = re.compile(r"^[_a-z]\w*?$", re.IGNORECASE)


class GreenTestLoader(unittest.TestLoader):
    """
    This class is responsible for loading tests according to various criteria
    and returning them wrapped in a GreenTestSuite. The super class wraps with
    TestSuite.
    """

    suiteClass: Type[GreenTestSuite] = GreenTestSuite

    def loadTestsFromTestCase(
        self, testCaseClass: Type[unittest.TestCase]
    ) -> GreenTestSuite:
        debug(f"Examining test case {testCaseClass.__name__}", 3)

        def filter_test_methods(attrname: str) -> bool:
            return (
                attrname.startswith(self.testMethodPrefix)
                and callable(getattr(testCaseClass, attrname))
                and not isTestCaseDisabled(testCaseClass, attrname)
            )

        test_case_names = list(filter(filter_test_methods, dir(testCaseClass)))
        debug(f"Test case names: {test_case_names}")

        # Use default unittest.TestSuite sorting method if not overridden
        test_case_names.sort(key=functools.cmp_to_key(self.sortTestMethodsUsing))

        if not test_case_names and hasattr(testCaseClass, "runTest"):
            test_case_names = ["runTest"]
        return flattenTestSuite(testCaseClass(name) for name in test_case_names)

    def loadFromModuleFilename(self, filename: str) -> TestSuite:
        dotted_module, parent_dir = findDottedModuleAndParentDir(filename)
        # Adding the parent path of the module to the start of sys.path is
        # the closest we can get to an absolute import in Python that I can
        # find.
        sys.path.insert(0, parent_dir)
        try:
            __import__(dotted_module)
            loaded_module = sys.modules[dotted_module]
            debug(f"Imported {dotted_module}", 2)
        except unittest.case.SkipTest as e:
            # TODO: #25 - Right now this mimics the behavior in unittest.  Lets
            # refactor it and simplify it after we make sure it works.
            # This is a cause of the traceback mangling I observed.
            reason = str(e)

            @unittest.case.skip(reason)
            def testSkipped(self):
                pass  # pragma: no cover

            TestClass = type(
                "ModuleSkipped", (unittest.case.TestCase,), {filename: testSkipped}
            )
            return self.suiteClass((TestClass(filename),))
        except:
            # TODO: #25 - Right now this mimics the behavior in unittest.  Lets
            # refactor it and simplify it after we make sure it works.
            # This is a cause of the traceback mangling I observed.
            message = ("Failed to import {} computed from filename {}\n{}").format(
                dotted_module, filename, traceback.format_exc()
            )

            def testFailure(self) -> None:
                raise ImportError(message)

            TestClass = type(
                "ModuleImportFailure",
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

    def loadTestsFromModule(  # type: ignore[override]
        self, module: ModuleType, *, pattern: str | None = None
    ) -> GreenTestSuite:
        tests = super().loadTestsFromModule(module, pattern=pattern)
        return flattenTestSuite(tests, module)

    def loadTestsFromName(
        self, name: str, module: ModuleType | None = None
    ) -> GreenTestSuite:
        tests = super().loadTestsFromName(name, module)
        return flattenTestSuite(tests, module)

    # TODO: In unittest/loader.py this is not supposed to return None but it
    #  always returns self.suiteClass(tests). Maybe we should do the same by
    #  returning GreenTestSuite() but empty instead. It might be possible that
    #  this is what is triggering the failures when running tests with the
    #  @skipIf decorator with 3.12.1.
    def discover(  # type: ignore[override]
        self,
        current_path: str,
        file_pattern: str = "test*.py",
        top_level_dir: str | None = None,
    ) -> GreenTestSuite | None:
        """
        I take a path to a directory and discover all the tests inside files
        matching file_pattern.

        If path is not a readable directory, I raise an ImportError.

        If I don't find anything, I return None.  Otherwise I return a
        GreenTestSuite
        """
        current_abspath = os.path.abspath(current_path)
        if not os.path.isdir(current_abspath):
            raise ImportError(f"'{current_path}' is not a directory")
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
            debug(f"WARNING: Test discovery failed at path {current_path}")

        return flattenTestSuite(suite) if suite.countTestCases() else None

    def loadTargets(
        self, targets: Iterable[str] | str, file_pattern: str = "test*.py"
    ) -> GreenTestSuite | None:
        """
        Load the given test targets. This is green specific and not part of unittest.TestLoader.
        """
        # If a string was passed in, put it into a tuple.
        if isinstance(targets, str):
            targets = [targets]

        # Make sure there are no duplicate entries, preserving order
        target_dict = {}
        for target in targets:
            target_dict[target] = True
        targets = target_dict.keys()

        suites: list[GreenTestSuite] = []
        for target in targets:
            suite = self.loadTarget(target, file_pattern)
            if not suite:
                debug(f"Found 0 tests for target '{target}'")
                continue
            suites.append(suite)
            num_tests = suite.countTestCases()
            debug(
                "Found {} test{} for target '{}'".format(
                    num_tests, "" if (num_tests == 1) else "s", target
                )
            )

        return flattenTestSuite(suites) if suites else None

    def loadTarget(
        self, target: str, file_pattern: str = "test*.py"
    ) -> GreenTestSuite | None:
        """
        Load the given test target. This is green specific and not part of unittest.TestLoader.
        """
        debug(
            f"Attempting to load target '{target}' with file_pattern '{file_pattern}'."
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
                if filename and "__init__.py" in filename:
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
                debug(f"Load method: DISCOVER - {candidate}")
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
                raise Exception(f"Exception while loading {target}: {e}")
            if tests and tests.countTestCases():
                debug(f"Load method: DOTTED OBJECT - {target}")
                return flattenTestSuite(tests)

        # FILE VARIATIONS - These will import a specific file and any tests
        # accessible from its scope.

        # some/file.py
        bare_file = target
        # some/file
        pyless_file = target + ".py"
        for candidate in (bare_file, pyless_file):
            if (candidate is None) or (not os.path.isfile(candidate)):
                continue
            need_cleanup = False
            cwd = os.getcwd()
            if cwd != sys.path[0]:
                need_cleanup = True
                # TODO: look into how much larger we grow sys.path with each
                #  candidate. It is possible that we end up with a lot of
                #  duplicate entries that might make imports slower.
                #  This is because sys.path.remove(cwd) is not in a Finally block.
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

                def testFailure(self) -> None:
                    raise ImportError(message)  # pragma: no cover

                TestClass = type(
                    "ModuleImportFailure",
                    (unittest.case.TestCase,),
                    {dotted_path: testFailure},
                )
                return self.suiteClass((TestClass(dotted_path),))
            if need_cleanup:
                # TODO: this might need to be in a finally block.
                sys.path.remove(cwd)
            if tests and tests.countTestCases():
                debug(f"Load method: FILE - {candidate}")
                return tests

        return None


def toProtoTestList(
    suite, test_list=None, doing_completions: bool = False
) -> list[result.ProtoTest]:
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
            test_list.append(result.proto_test(suite))
    else:
        for i in suite:
            toProtoTestList(i, test_list, doing_completions)
    return test_list


def toParallelTargets(suite: GreenTestSuite, targets: Iterable[str]) -> list[str]:
    """
    Produce a list of targets which should be tested in parallel.

    For the most part, this will be a list of test modules.
    The exception is when a dotted name representing something more granular
    than a module was input (like an individual test case or test method).

    This is green specific and not part of unittest/loader.py.
    """
    if isinstance(targets, str):
        # This should not happen, but mypy treats str as a valid sequence of strings.
        targets = (targets,)
    targets = (x for x in targets if x != ".")
    # First, convert the suite to a proto test list - proto tests nicely
    # parse things like the fully dotted name of the test and the
    # finest-grained module it belongs to, which simplifies our job.
    proto_test_list = toProtoTestList(suite)
    # Extract a list of the modules that all of the discovered tests are in
    modules = {x.module for x in proto_test_list}
    # Get the list of user-specified targets that are NOT modules
    non_module_targets = []
    target: str
    for target in targets:
        if not list(filter(None, (target in x for x in modules))):
            non_module_targets.append(target)
    # Main loop -- iterating through all loaded test methods
    parallel_targets: list[str] = []
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


def getCompletions(target: list[str] | str) -> str:
    # This option expects 0 or 1 targets
    if not isinstance(target, str):
        target = target[0]
    if target == ".":
        target = ""

    # Discover tests and load them into a suite

    # First try the completion as-is.  It might be at a valid spot.
    loader = GreenTestLoader()
    # FIXME: We do not pass file_pattern here, ignoring `--file-pattern`?
    test_suite = loader.loadTargets(target)
    if not test_suite:
        # Next, try stripping to the previous '.'
        last_dot_idx = target.rfind(".")
        to_complete: str | Iterable[str] = ""
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
                else:  # pragma: no cover -- occurs in Python <= 3.7, but can't find a reasonable way to cover this line when it doesn't in Python > 3.7
                    break
    return "\n".join(sorted(list(dotted_names)))


def isPackage(file_path: pathlib.Path) -> bool:
    """
    Determine whether or not a given path is a (sub)package or not. Green specific.
    """
    return file_path.is_dir() and (file_path / "__init__.py").is_file()


def findDottedModuleAndParentDir(file_path: str | pathlib.Path) -> tuple[str, str]:
    """
    I return a tuple (dotted_module, parent_dir) where dotted_module is the
    full dotted name of the module with respect to the package it is in, and
    parent_dir is the absolute path to the parent directory of the package.

    For filepath '/a/b/c/d.py' where b is the package, ('b.c.d', '/a')
    would be returned.

    This is green specific and not part of unittest/loader.py.
    """
    path = pathlib.Path(file_path)
    if not path.is_file():
        raise ValueError(f"'{file_path}' is not a file.")
    parent_dir = path.absolute().parent
    dotted_module = path.stem
    while isPackage(parent_dir):
        dotted_module = f"{parent_dir.stem}.{dotted_module}"
        parent_dir = parent_dir.parent
    debug(f"Dotted module: {parent_dir} -> {dotted_module}", 2)
    # TODO: consider returning the Path object for the parent directory.
    return dotted_module, str(parent_dir)


def isTestCaseDisabled(test_case_class: Type[TestCase], method_name: str) -> bool:
    """
    I check to see if a method on a TestCase has been disabled via nose's
    convention for disabling a TestCase.  This makes it so that users can
    mix nose's parameterized tests with green as a runner.
    """
    test_method = getattr(test_case_class, method_name)
    return getattr(test_method, "__test__", "not nose") is False


def flattenTestSuite(
    test_suite: Iterable[FlattenableTests | TestCase] | FlattenableTests | TestCase,
    module: ModuleType | None = None,
) -> GreenTestSuite:
    """
    Look for a `doctest_modules` list and attempt to add doctest tests to the
    suite of tests that we are about to flatten. Green specific.
    """
    # todo: rename this function to something more appropriate.
    suites: list[Iterable[FlattenableTests | TestCase] | FlattenableTests | TestCase]
    suites = [test_suite]
    doctest_modules = getattr(module, "doctest_modules", ())
    for doctest_module in doctest_modules:
        doc_suite = DocTestSuite(doctest_module)
        # Forcing an injected_module onto DocTestSuite.
        doc_suite.injected_module = module.__name__  # type: ignore
        suites.append(doc_suite)

    # Now extract all tests from the suite hierarchies and flatten them into a
    # single suite with all tests.
    tests: list[TestSuite | GreenTestSuite | TestCase] = []
    for suite in suites:
        # injected_module is not present in DocTestSuite.
        injected_module: str | None = getattr(suite, "injected_module", None)
        # We might have received an iterable of TestCase instances from loadTestsFromTestCase().
        # If this happens iterating over it should not be possible. This will
        # require further investigation.
        for test in suite:  # type: ignore
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
