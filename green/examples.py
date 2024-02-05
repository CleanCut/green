from __future__ import annotations

import sys
import unittest
from typing import Final

doctest_modules: Final[list[str]] = ["green.examples"]


class TestStates(unittest.TestCase):
    def test0Pass(self) -> None:
        """
        This test will print output to stdout, and then pass.
        """
        print("Sunshine and daisies")

    def test1Fail(self) -> None:
        """
        This test will print output to stderr, and then fail an assertion.
        """
        sys.stderr.write("Doom and gloom.\n")
        self.assertTrue(False)

    def test2Error(self) -> None:
        """
        An Exception will be raised (and not caught) while running this test.
        """
        raise Exception

    @unittest.skip("This is the 'reason' portion of the skipped test.")
    def test3Skip(self) -> None:
        """
        This test will be skipped.
        """
        pass

    @unittest.expectedFailure
    def test4ExpectedFailure(self) -> None:
        """
        This test will fail, but we expect it to.
        """
        self.assertEqual(True, False)

    @unittest.expectedFailure
    def test5UnexpectedPass(self) -> None:
        """
        This test will pass, but we expected it to fail!
        """
        pass


def some_function() -> int:
    """
    This will fail because some_function() does not, in fact, return 100.
    >>> some_function()
    100
    """
    return 99


class MyClass:
    def my_method(self) -> str:
        """
        This will pass.
        >>> s = MyClass()
        >>> s.my_method()
        'happy'
        """
        return "happy"
