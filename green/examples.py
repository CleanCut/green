from __future__ import unicode_literals
import sys
import unittest



class TestStates(unittest.TestCase):


    def test0Pass(self):
        """
        This test will print output to stdout, and then pass.
        """
        print("Sunshine and daisies")


    def test1Fail(self):
        """
        This test will print output to stderr, and then fail an assertion
        """
        sys.stderr.write("Doom and gloom.\n")
        self.assertTrue(False)


    def test2Error(self):
        """
        An Exception will be raised (and not caught) while running this test.
        """
        raise Exception


    @unittest.skip("This is the 'reason' portion of the skipped test.")
    def test3Skip(self):
        """
        This test will be skipped.
        """
        pass

    @unittest.expectedFailure
    def test4ExpectedFailure(self):
        """
        This test will fail, but we expect it to.
        """
        self.assertEqual(True, False)


    @unittest.expectedFailure
    def test5UnexpectedPass(self):
        """
        This test will pass, but we expected it to fail!
        """
        pass
