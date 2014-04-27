import time
import unittest



class TestNormalStates(unittest.TestCase):


    def test0Pass(self):
        return


    def test1Fail(self):
        self.assertTrue(False)


    def test2Error(self):
        raise Exception


    @unittest.skip("Skipping for fun.")
    def test3Skip(self):
        pass

    @unittest.expectedFailure
    def test4ExpectedFailure(self):
        self.assertEqual(True, False)


    @unittest.expectedFailure
    def test5UnexpectedPass(self):
        pass



class TestOutputBeforeAndAfter(unittest.TestCase):


    def testTimed0(self):
        time.sleep(.2)


    def testTimed1(self):
        time.sleep(.2)


    def testTimed2(self):
        time.sleep(.2)


    def testTimed3(self):
        time.sleep(.2)


    def testTimed4(self):
        time.sleep(.2)


    def testTimed5(self):
        time.sleep(.2)


