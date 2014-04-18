import time
import unittest



class TestNormalStates(unittest.TestCase):


    def test_pass(self):
        return


    def test_error(self):
        raise Exception


    def test_fail(self):
        self.assertTrue(False)


    @unittest.skip("Skipping for fun.")
    def test_skip(self):
        pass


class TestOutputBeforeAndAfter(unittest.TestCase):


    def test_pass0(self):
        time.sleep(.1)


    def test_pass0b(self):
        time.sleep(.1)


    def test_pass1(self):
        time.sleep(.2)


    def test_pass2(self):
        time.sleep(.2)


    def test_pass3(self):
        time.sleep(.3)


    def test_pass4(self):
        time.sleep(.3)


    def test_simpleError(self):
        time.sleep(.4)
        raise Exception


    def test_simpleFail(self):
        time.sleep(.4)
        self.assertTrue(False)
