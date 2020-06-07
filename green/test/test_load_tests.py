from __future__ import unicode_literals

import os
import shutil
import tempfile
import unittest
import textwrap

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty

from green.loader import GreenTestLoader
from green.process import poolRunner
from green import process


class TestLoadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.startdir = os.getcwd()
        cls.container_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.startdir)
        # shutil.rmtree(cls.container_dir)

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(dir=self.container_dir)
        self.sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        self.basename = os.path.basename(self.sub_tmpdir)
        os.chdir(self.tmpdir)

        with open(os.path.join(self.basename, "__init__.py"), "w") as f:
            f.write("\n")

    def tearDown(self):
        os.chdir(self.container_dir)
        shutil.rmtree(self.tmpdir)

    def test_monkey_patch(self):
        """
        Check that monkey-patching a TestCase in the load_tests function
        actually changes the referenced class.
        """

        with open(
            os.path.join(self.basename, "test_load_tests_monkeypatch.py"), "w"
        ) as f:
            f.write(
                textwrap.dedent(
                    """
                import unittest
                class A(unittest.TestCase):
                    passing = False
                    def test_that_will_fail(self):
                        self.assertTrue(self.passing)

                def load_tests(loader, tests, pattern):
                    A.passing = True
                    return tests
                """
                )
            )

        module_name = self.basename + ".test_load_tests_monkeypatch"
        result = Queue()
        poolRunner(module_name, result, 0)
        result.get()

        proto_test_result = result.get()
        self.assertEqual(len(proto_test_result.passing), 1)
        self.assertEqual(len(proto_test_result.failures), 0)
        self.assertEqual(len(proto_test_result.errors), 0)
        self.assertEqual(proto_test_result.passing[0].class_name, "A")

    def test_foreign_suite(self):
        """
        Load tests does not reuse the tests and instead returns
        another TestSuite (or maybe not even a unittest.TestSuite).
        """

        with open(
            os.path.join(self.basename, "test_load_keys_foreign_suite.py"), "w"
        ) as f:
            f.write(
                textwrap.dedent(
                    """
                import unittest
                class A(unittest.TestCase):
                    def test_that_will_fail(self):
                        self.fail()

                def load_tests(loader, tests, pattern):
                    class B(unittest.TestCase):
                        def test_that_succeeds(self):
                            pass
                    suite = unittest.TestSuite()
                    suite.addTests(loader.loadTestsFromTestCase(B))
                    return suite
                """
                )
            )

        module_name = self.basename + ".test_load_keys_foreign_suite"
        result = Queue()
        poolRunner(module_name, result, 0)
        result.get()

        proto_test_result = result.get()
        self.assertEqual(len(proto_test_result.passing), 1)
        self.assertEqual(len(proto_test_result.errors), 0)
        self.assertEqual(len(proto_test_result.failures), 0)
        self.assertEqual(proto_test_result.passing[0].class_name, "B")

    def test_none_cancels(self):
        """
        Check that if load_tests returns None, no tests are run.
        """
        with open(
            os.path.join(self.basename, "test_load_keys_none_cancels.py"), "w"
        ) as fh:
            fh.write(
                textwrap.dedent(
                    """
                import unittest
                class A(unittest.TestCase):
                    def test_that_will_fail(self):
                        self.fail()

                def load_tests(loader, tests, pattern):
                    return None
                """
                )
            )

        module_name = self.basename + ".test_load_keys_none_cancels"
        result = Queue()
        poolRunner(module_name, result, 0)
        result.get()

        proto_test_result = result.get()
        self.assertEqual(len(proto_test_result.errors), 1)
        self.assertEqual(len(proto_test_result.passing), 0)
        self.assertEqual(len(proto_test_result.failures), 0)

    def test_additive(self):
        """
        Check that adding tests to the `tests` argument of the load_tests
        function add more tests to be run.
        """

        with open(os.path.join(self.basename, "test_load_keys_additive.py"), "w") as fh:
            fh.write(
                textwrap.dedent(
                    """
                import unittest
                class A(unittest.TestCase):
                    def test_that_will_succeed(self):
                        pass

                class B(unittest.TestCase):
                    def test_clear_sight(self):
                        self.fail()

                    def _hidden_test(self):
                        pass

                def load_tests(loader, tests, pattern):
                    setattr(B, 'test_that_will_succeed', B._hidden_test)
                    tests.addTests(loader.loadTestsFromTestCase(B))
                    return tests
                """
                )
            )

        loader = GreenTestLoader()
        test_suite = loader.loadTargets(self.basename + "." + "test_load_keys_additive")
        self.assertEqual(len(test_suite._tests), 4)  # a + b1 + b1 + b2
