from __future__ import unicode_literals
import unittest



class TestStates(unittest.TestCase):


    def test0Pass(self):
        return


    def test1Fail(self):
        self.assertTrue(False)


    def test2Error(self):
        raise Exception


    @unittest.skip("Testing skip functionality.")
    def test3Skip(self):
        pass

    @unittest.expectedFailure
    def test4ExpectedFailure(self):
        self.assertEqual(True, False)


    @unittest.expectedFailure
    def test5UnexpectedPass(self):
        pass


