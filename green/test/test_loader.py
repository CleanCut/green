from __future__ import unicode_literals
import os
from os.path import dirname
import platform
import shutil
import sys
import tempfile
from textwrap import dedent
import unittest
try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock

from green import loader
from green.loader import GreenTestLoader


class TestToProtoTestList(unittest.TestCase):

    def test_moduleImportFailure(self):
        """
        toProtoTestList() raises import errors normally
        """
        suite = MagicMock()
        suite.__class__.__name__ = str('ModuleImportFailure')
        suite.__str__.return_value = "exception_method other_stuff"
        suite.exception_method.side_effect = AttributeError
        self.assertRaises(AttributeError, loader.toProtoTestList, (suite,))

    def test_moduleImportFailureIgnored(self):
        """
        toProtoTestList() does not raise errors when doing completions
        """
        suite = MagicMock()
        suite.__class__.__name__ = str('ModuleImportFailure')
        suite.__str__.return_value = "exception_method other_stuff"
        suite.exception_method.side_effect = AttributeError
        self.assertEqual(loader.toProtoTestList(suite, doing_completions=True), [])


class TestToParallelTargets(unittest.TestCase):

    def setUp(self):
        super(TestToParallelTargets, self).setUp()

        class FakeModule(object):
            pass

        class FakeModule2(object):
            pass

        self._fake_module_name = "my_test_module"
        self._fake_module_name2 = "my_test_module2"
        sys.modules[self._fake_module_name] = FakeModule
        sys.modules[self._fake_module_name2] = FakeModule2

    def tearDown(self):
        del sys.modules[self._fake_module_name]
        del sys.modules[self._fake_module_name2]
        super(TestToParallelTargets, self).tearDown()

    def test_methods_with_no_constraints(self):
        """
        toParallelTargets() returns only module names.
        """
        class NormalTestCase(unittest.TestCase):
            def runTest(self):
                pass

        NormalTestCase.__module__ = self._fake_module_name

        targets = loader.toParallelTargets(NormalTestCase(), [])
        self.assertEqual(targets, ["my_test_module"])

    def test_methods_with_constraints(self):
        """
        toParallelTargets() returns test names when constrained.
        """
        class NormalTestCase(unittest.TestCase):
            def runTest(self):
                pass

        NormalTestCase.__module__ = self._fake_module_name
        full_name = "my_test_module.NormalTestCase.runTest"

        targets = loader.toParallelTargets(NormalTestCase(), [full_name])
        self.assertEqual(targets, [full_name])

    def test_filter_out_dot(self):
        """
        toParallelTargets() correctly returns modules when '.' is in target list
        """
        class NormalTestCase(unittest.TestCase):
            def runTest(self):
                pass

        class NormalTestCase2(unittest.TestCase):
            def runTest(self):
                pass

        NormalTestCase.__module__ = self._fake_module_name
        NormalTestCase2.__module__ = self._fake_module_name2

        targets = loader.toParallelTargets([NormalTestCase(), NormalTestCase2()], ['.'])
        self.assertEqual(targets, ["my_test_module", "my_test_module2"])


class TestCompletions(unittest.TestCase):

    def test_completionBad(self):
        """
        Bad match generates no completions
        """
        self.assertEqual('', loader.getCompletions('garbage.in'))

    def test_completionExact(self):
        """
        Correct completions are generated for an exact match.
        """
        c = set(loader.getCompletions('green').split('\n'))
        self.assertIn('green', c)
        self.assertIn('green.test', c)
        self.assertIn('green.test.test_loader', c)
        self.assertIn('green.test.test_loader.TestCompletions', c)
        self.assertIn(
                'green.test.test_loader.TestCompletions.test_completionExact', c)

    def test_completionPartialShort(self):
        """
        Correct completions generated for short partial match.
        """
        cwd = os.getcwd()
        green_parent = dirname(dirname(dirname(os.path.abspath(__file__))))
        os.chdir(green_parent)
        self.addCleanup(os.chdir, cwd)
        c = set(loader.getCompletions('gre').split('\n'))
        self.assertIn('green', c)
        self.assertIn('green.test', c)
        self.assertIn('green.test.test_loader', c)
        self.assertIn('green.test.test_loader.TestCompletions', c)
        self.assertIn(
            'green.test.test_loader.TestCompletions.test_completionPartialShort', c)

    def test_completionPartial(self):
        """
        Correct completions generated for partial match.  2nd target ignored.
        """
        c = set(loader.getCompletions(['green.te', 'green']).split('\n'))
        self.assertIn('green.test', c)
        self.assertIn('green.test.test_loader', c)
        self.assertIn('green.test.test_loader.TestCompletions', c)
        self.assertIn(
            'green.test.test_loader.TestCompletions.test_completionPartial', c)
        self.assertNotIn('green', c)

    def test_completionEmpty(self):
        """
        An empty target generates completions for the whole directory
        """
        cwd = os.getcwd()
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        os.chdir(tmpdir)
        self.addCleanup(os.chdir, cwd)
        os.mkdir('the_pkg')
        fh = open(os.path.join('the_pkg', '__init__.py'), 'w')
        fh.write('')
        fh.close()
        fh = open(os.path.join('the_pkg', 'test_things.py'), 'w')
        fh.write(dedent(
            """
            import unittest

            class A(unittest.TestCase):
                def testOne(self):
                    pass
                def testTwo(self):
                    pass
            """))
        fh.close()
        c = set(loader.getCompletions('').split('\n'))
        self.assertIn('the_pkg', c)
        self.assertIn('the_pkg.test_things', c)
        self.assertIn('the_pkg.test_things.A.testOne', c)
        self.assertIn('the_pkg.test_things.A.testTwo', c)

    def test_completionDot(self):
        """
        A '.' target generates completions for the whole directory
        """
        cwd = os.getcwd()
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        os.chdir(tmpdir)
        self.addCleanup(os.chdir, cwd)
        os.mkdir('my_pkg')
        fh = open(os.path.join('my_pkg', '__init__.py'), 'w')
        fh.write('')
        fh.close()
        fh = open(os.path.join('my_pkg', 'test_things.py'), 'w')
        fh.write(dedent(
            """
            import unittest

            class A(unittest.TestCase):
                def testOne(self):
                    pass
                def testTwo(self):
                    pass
            """))
        fh.close()
        c = set(loader.getCompletions('.').split('\n'))
        self.assertIn('my_pkg', c)
        self.assertIn('my_pkg.test_things', c)
        self.assertIn('my_pkg.test_things.A.testOne', c)
        self.assertIn('my_pkg.test_things.A.testTwo', c)

    def test_completionIgnoresErrors(self):
        """
        Errors in one module don't block the remaining completions
        """
        cwd = os.getcwd()
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        os.chdir(tmpdir)
        self.addCleanup(os.chdir, cwd)
        os.mkdir('my_pkg2')
        fh = open(os.path.join('my_pkg2', '__init__.py'), 'w')
        fh.write('')
        fh.close()
        fh = open(os.path.join('my_pkg2', 'test_crash01.py'), 'w')
        contents = dedent(
            """
            import unittest

            class A(unittest.TestCase):
                def testOne(self):
                    pass
                def testTwo(self):
                    pass
            """)
        fh.write(contents)
        fh.close()
        fh = open(os.path.join('my_pkg2', 'test_crash02.py'), 'w')
        fh.write("import moocow")
        fh.close()
        fh = open(os.path.join('my_pkg2', 'test_crash03.py'), 'w')
        fh.write(contents)
        fh.close()
        c = set(loader.getCompletions('.').split('\n'))
        self.assertIn('my_pkg2', c)
        self.assertIn('my_pkg2.test_crash01', c)
        self.assertIn('my_pkg2.test_crash01.A.testOne', c)
        self.assertIn('my_pkg2.test_crash01.A.testTwo', c)
        self.assertIn('my_pkg2.test_crash03', c)
        self.assertIn('my_pkg2.test_crash03.A.testOne', c)
        self.assertIn('my_pkg2.test_crash03.A.testTwo', c)


class TestIsPackage(unittest.TestCase):

    def test_yes(self):
        """
        A package is identified.
        """
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        fh = open(os.path.join(tmpdir, '__init__.py'), 'w')
        fh.write('pass\n')
        fh.close()
        self.assertTrue(loader.isPackage(tmpdir))

    def test_no(self):
        """
        A non-package is identified
        """
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        self.assertFalse(loader.isPackage(tmpdir))


class TestDottedModule(unittest.TestCase):

    def test_bad_path(self):
        """
        A bad path causes an exception
        """
        self.assertRaises(
                ValueError,
                loader.findDottedModuleAndParentDir,
                tempfile.tempdir)

    def test_good_path(self):
        """
        A good path gets (dotted_module, parent) properly returned
        """
        tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmpdir, 'a', 'b', 'c', 'd'))
        package_init = os.path.join(tmpdir, 'a', 'b', 'c', '__init__.py')
        subpkg_init = os.path.join(tmpdir, 'a', 'b', 'c', 'd', '__init__.py')
        module_name = 'stuff.py'
        module = os.path.join(tmpdir, 'a', 'b', 'c', 'd', module_name)
        for filename in [package_init, subpkg_init, module]:
            fh = open(filename, 'w')
            fh.write('pass\n')
            fh.close()
        self.assertEqual(loader.findDottedModuleAndParentDir(module),
                         ('c.d.stuff', os.path.join(tmpdir, 'a', 'b')))


class TestLoadTestsFromTestCase(unittest.TestCase):

    def setUp(self):
        self.loader = GreenTestLoader()

    def test_runTest(self):
        """
        When a testcase has no matching method names, but does have a runTest,
        use that instead.
        """
        class MyTestCase(unittest.TestCase):
            def helper1(self):
                pass

            def helper2(self):
                pass

            def runTest(self):
                pass

        suite = self.loader.loadTestsFromTestCase(MyTestCase)
        self.assertEqual(suite.countTestCases(), 1)
        self.assertEqual(suite._tests[0]._testMethodName, 'runTest')

    def test_normal(self):
        """
        Normal test methods get loaded
        """
        class Normal(unittest.TestCase):
            def test_method1(self):
                pass

            def test_method2(self):
                pass

        suite = self.loader.loadTestsFromTestCase(Normal)
        self.assertEqual(suite.countTestCases(), 2)
        self.assertEqual(set([x._testMethodName for x in suite._tests]),
                         set(['test_method1', 'test_method2']))

    def test_isTestCaseDisabled(self):
        """
        TestCases disabled by nose generators don't get loaded
        """
        class HasDisabled(unittest.TestCase):
            def test_method(self):
                pass

            test_method.__test__ = False

        suite = self.loader.loadTestsFromTestCase(HasDisabled)
        self.assertEqual(suite.countTestCases(), 0)


class TestLoadFromModuleFilename(unittest.TestCase):

    def setUp(self):
        self.loader = GreenTestLoader()

    def test_skipped_module(self):
        """
        A module that wants to be skipped gets skipped
        """
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        filename = os.path.join(tmpdir, 'skipped_module.py')
        fh = open(filename, 'w')
        fh.write(dedent(
            """
            import unittest
            raise unittest.case.SkipTest
            class NotReached(unittest.TestCase):
                def test_one(self):
                    pass
                def test_two(self):
                    pass
            """))
        fh.close()
        suite = self.loader.loadFromModuleFilename(filename)
        self.assertEqual(suite.countTestCases(), 1)
        self.assertRaises(unittest.case.SkipTest,
                          getattr(suite._tests[0],
                                  suite._tests[0]._testMethodName))


class TestDiscover(unittest.TestCase):

    def setUp(self):
        self.loader = GreenTestLoader()

    def test_bad_input(self):
        """
        discover() raises ImportError when passed a non-directory
        """
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        self.assertRaises(ImportError, self.loader.discover,
                          os.path.join(tmpdir, 'garbage_in'))
        filename = os.path.join(tmpdir, 'some_file.py')
        fh = open(filename, 'w')
        fh.write('pass\n')
        fh.close()
        self.assertRaises(ImportError, self.loader.discover, filename)

    def test_bad_pkg_name(self):
        """
        If the directory is an invalid package name, don't bother looking in
        it.
        """
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        startdir = os.getcwd()
        os.chdir(tmpdir)
        self.addCleanup(os.chdir, startdir)
        bad_pkg_name = '1badname'
        os.mkdir(bad_pkg_name)
        tmp_subdir = os.path.join(tmpdir, bad_pkg_name)
        fh = open(os.path.join(tmp_subdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        named_module = os.path.join(os.path.basename(tmp_subdir),
                                    'named_module.py')
        fh = open(named_module, 'w')
        fh.write(dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPass(self):
                    pass
            """))
        fh.close()
        self.assertEqual(self.loader.discover(tmpdir), None)

    def test_symlink(self):
        """
        If the directory is a symlink, it should be skipped.
        """
        if platform.system() == 'Windows':  # pragma: no cover
            self.skipTest('This test is for posix-specific behavior')
        tmpdir  = tempfile.mkdtemp()
        tmpdir2 = tempfile.mkdtemp()
        os.symlink(tmpdir, os.path.join(tmpdir2, 'link'))
        self.addCleanup(shutil.rmtree, tmpdir)
        startdir = os.getcwd()
        os.chdir(tmpdir)
        self.addCleanup(os.chdir, startdir)
        pkg_name = 'realpkg'
        os.mkdir(pkg_name)
        tmp_subdir = os.path.join(tmpdir, pkg_name)
        fh = open(os.path.join(tmp_subdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        named_module = os.path.join(os.path.basename(tmp_subdir),
                                    'test_module.py')
        fh = open(named_module, 'w')
        fh.write(dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPass(self):
                    pass
            """))
        fh.close()
        self.assertEqual(self.loader.discover(tmpdir2), None)


class TestLoadTargets(unittest.TestCase):

    # Setup
    @classmethod
    def setUpClass(cls):
        cls.startdir = os.getcwd()
        cls.container_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        if os.getcwd() != cls.startdir:
            os.chdir(cls.startdir)
        cls.startdir = None
        shutil.rmtree(cls.container_dir)

    def setUp(self):
        os.chdir(self.container_dir)
        self.tmpdir = tempfile.mkdtemp(dir=self.container_dir)
        self.loader = GreenTestLoader()

    def tearDown(self):
        os.chdir(self.container_dir)
        shutil.rmtree(self.tmpdir)

    # Tests
    def test_returnIsLoadable(self):
        """
        Results returned by toParallelTargets should be loadable by
        loadTargets(), even if they aren't directly loadable through a package
        relative to the current working directory.
        """
        tests_dir = tempfile.mkdtemp(dir=self.tmpdir)
        # No __init__.py in the directory!
        fh = open(os.path.join(tests_dir, 'test_not_in_pkg.py'), 'w')
        fh.write(dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPass(self):
                    pass
            """
            ))
        fh.close()
        # Discover stuff
        suite = self.loader.loadTargets('.')
        # This should resolve it to the module that's not importable from here
        test =loader.toParallelTargets(suite, [])[0]
        self.loader.loadTargets(test)

    def test_emptyDirAbsolute(self):
        """
        Absolute path to empty directory returns None
        """
        tests = self.loader.loadTargets(self.tmpdir)
        self.assertTrue(tests is None)

    def test_emptyDirRelative(self):
        """
        Relative path to empty directory returns None
        """
        os.chdir(self.tmpdir)
        os.chdir('..')
        tests = self.loader.loadTargets(os.path.dirname(self.tmpdir))
        self.assertEqual(tests, None)

    def test_emptyDirDot(self):
        """
        '.' while in an empty directory returns None
        """
        os.chdir(self.tmpdir)
        tests = self.loader.loadTargets('.')
        self.assertTrue(tests is None)

    def test_relativeDotDir(self):
        """
        Dotted relative path to empty directory returns None
        """
        os.chdir(self.tmpdir)
        os.chdir('..')
        target = os.path.join('.', os.path.basename(self.tmpdir))
        tests = self.loader.loadTargets(target)
        self.assertTrue(tests is None)

    def test_BigDirWithAbsoluteImports(self):
        """
        Big dir discovers tests and doesn't crash on absolute import
        """
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        pkg_name = os.path.basename(sub_tmpdir)
        # Child setup
        # pkg/__init__.py
        fh = open(os.path.join(sub_tmpdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        # pkg/target_module.py
        fh = open(os.path.join(sub_tmpdir, 'target_module.py'), 'w')
        fh.write('a = 1\n')
        fh.close()
        # pkg/test/__init__.py
        os.mkdir(os.path.join(sub_tmpdir, 'test'))
        fh = open(os.path.join(sub_tmpdir, 'test', '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        # pkg/test/test_target_module.py
        fh = open(os.path.join(sub_tmpdir, 'test', 'test_target_module.py'), 'w')
        fh.write(dedent(
            """
            import unittest
            import {}.target_module
            class A(unittest.TestCase):
                def testPass(self):
                    pass
            """.format(pkg_name)))
        fh.close()
        # Load the tests
        os.chdir(self.tmpdir)
        test_suite = self.loader.loadTargets(pkg_name)
        self.assertEqual(test_suite.countTestCases(), 1)
        # Dotted name should start with the package!
        self.assertEqual(
                pkg_name + '.test.test_target_module.A.testPass',
                loader.toProtoTestList(test_suite)[0].dotted_name)

    def test_DirWithInit(self):
        """
        Dir empty other than blank __init__.py returns None
        """
        # Parent directory setup
        os.chdir(self.tmpdir)
        os.chdir('..')
        # Child setup
        target = os.path.join(self.tmpdir, '__init__.py')
        fh = open(target, 'w')
        fh.write('\n')
        fh.close()
        fh = open(os.path.join(self.tmpdir, 'test_module_with_init.py'), 'w')
        fh.write(dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPass(self):
                    pass
            """))
        fh.close()
        # Load the tests
        module_name = os.path.basename(self.tmpdir)
        tests = self.loader.loadTargets(module_name)
        self.assertEqual(tests.countTestCases(), 1)

    def test_DottedName(self):
        """
        Importing a module via dotted name loads the tests.
        """
        # Parent directory setup
        os.chdir(self.tmpdir)
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        basename = os.path.basename(sub_tmpdir)
        # Child setup
        fh = open(os.path.join(basename, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        fh = open(os.path.join(basename, 'test_module_dotted_name.py'), 'w')
        fh.write(dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPass(self):
                    pass
            """))
        fh.close()
        # Load the tests
        module_name = basename + ".test_module_dotted_name"
        tests = self.loader.loadTargets(module_name)
        self.assertEqual(tests.countTestCases(), 1)

    def test_DottedNamePackageFromPath(self):
        """
        Importing a package from path loads the tests.
        """
        # Child setup

        tmp_subdir = tempfile.mkdtemp(dir=self.tmpdir)
        fh = open(os.path.join(tmp_subdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        fh = open(os.path.join(tmp_subdir, 'test_module.py'), 'w')
        fh.write(dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPass(self):
                    pass
            """))
        fh.close()
        # Go somewhere else, but setup the path
        os.chdir(self.startdir)
        sys.path.insert(0, self.tmpdir)
        # Load the tests
        tests = self.loader.loadTargets(os.path.basename(tmp_subdir))
        sys.path.remove(self.tmpdir)
        self.assertTrue(tests.countTestCases(), 1)

    def test_ModuleByName(self):
        """
        A module in a package can be loaded by filename.
        """
        os.chdir(self.tmpdir)
        tmp_subdir = tempfile.mkdtemp(dir=self.tmpdir)
        fh = open(os.path.join(tmp_subdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        named_module = os.path.join(os.path.basename(tmp_subdir),
                                    'named_module.py')
        fh = open(named_module, 'w')
        fh.write(dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPass(self):
                    pass
            """))
        fh.close()
        # Load the tests
        tests = self.loader.loadTargets(named_module)
        try:
            self.assertEqual(tests.countTestCases(), 1)
        except:
            raise
        finally:
            shutil.rmtree(tmp_subdir)

    def test_MalformedModuleByName(self):
        """
        Importing malformed module by name creates test that raises
        ImportError.
        """
        fh = open(os.path.join(self.tmpdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        malformed_module = os.path.join(os.path.basename(self.tmpdir),
                                        'malformed_module.py')
        fh = open(malformed_module, 'w')
        fh.write("This is a malformed module.")
        fh.close()
        # Load the tests
        tests = self.loader.loadTargets(malformed_module)
        self.assertEqual(tests.countTestCases(), 1)
        test = tests._tests[0]
        test_method = getattr(test, test._testMethodName)
        self.assertRaises(ImportError, test_method)

    def test_partiallyGoodName(self):
        """
        Don't crash loading module.object with existing module but not object.
        """
        # Parent directory setup
        os.chdir(self.tmpdir)
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        basename = os.path.basename(sub_tmpdir)
        # Child setup
        fh = open(os.path.join(basename, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        fh = open(os.path.join(basename, 'existing_module.py'), 'w')
        fh.write(dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPass(self):
                    pass
            """))
        fh.close()
        # Load the tests
        module_name = basename + ".existing_module.nonexistant_object"
        tests = self.loader.loadTargets(module_name)
        self.assertEqual(tests, None)

    def test_multiple_targets(self):
        """
        Specifying multiple targets causes them all to be tested.
        """
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        # pkg/__init__.py
        fh = open(os.path.join(sub_tmpdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        # pkg/test/test_target1.py
        fh = open(os.path.join(sub_tmpdir, 'test_target1.py'), 'w')
        fh.write(dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPasses(self):
                    pass
            """))
        fh.close()
        # pkg/test/test_target2.py
        fh = open(os.path.join(sub_tmpdir, 'test_target2.py'), 'w')
        fh.write(dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPasses(self):
                    pass
            """))
        fh.close()
        # Load the tests
        os.chdir(self.tmpdir)
        pkg = os.path.basename(sub_tmpdir)
        tests = self.loader.loadTargets([pkg + '.' + 'test_target1',
                                         pkg + '.' + 'test_target2'])
        self.assertEqual(tests.countTestCases(), 2)

    def test_duplicate_targets(self):
        """
        Specifying duplicate targets does not cause duplicate loading.
        """
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        fh = open(os.path.join(sub_tmpdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        fh = open(os.path.join(sub_tmpdir, 'test_dupe_target.py'), 'w')
        fh.write(dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPasses(self):
                    pass
            """))
        fh.close()

        os.chdir(self.tmpdir)
        pkg = os.path.basename(sub_tmpdir)
        tests = self.loader.loadTargets([pkg + '.' + 'test_dupe_target',
                                         pkg + '.' + 'test_dupe_target',
                                         pkg + '.' + 'test_dupe_target'])
        self.assertEqual(tests.countTestCases(), 1)

    def test_explicit_filename_error(self):
        """
        Loading a module by name with a syntax error produces a failure, not a
        silent absence of its tests.
        """
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        fh = open(os.path.join(sub_tmpdir, 'mod_with_import_error.py'), 'w')
        fh.write('this is a syntax error')
        fh.close()

        os.chdir(sub_tmpdir)
        tests = self.loader.loadTargets('mod_with_import_error.py')
        self.assertEqual(tests.countTestCases(), 1)

    def test_file_pattern(self):
        """
        Specifying a file pattern causes only matching files to be loaded
        """
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        # pkg/__init__.py
        fh = open(os.path.join(sub_tmpdir, '__init__.py'), 'w')
        fh.write('\n')
        fh.close()
        # pkg/test/target1_tests.py
        fh = open(os.path.join(sub_tmpdir, 'target1_tests.py'), 'w')
        fh.write(dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPasses(self):
                    pass
            """))
        fh.close()
        # pkg/test/target2_tests.py
        fh = open(os.path.join(sub_tmpdir, 'target2_tests.py'), 'w')
        fh.write(dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPasses(self):
                    pass
            """))
        fh.close()
        # pkg/test/test_target999.py: NOT a match.
        fh = open(os.path.join(sub_tmpdir, 'test_target999.py'), 'w')
        fh.write(dedent(
            """
            import unittest
            class A(unittest.TestCase):
                def testPasses(self):
                    pass
            """))
        fh.close()
        # Load the tests
        os.chdir(self.tmpdir)
        pkg = os.path.basename(sub_tmpdir)
        tests = self.loader.loadTargets(pkg, file_pattern='*_tests.py')
        self.assertEqual(tests.countTestCases(), 2)
