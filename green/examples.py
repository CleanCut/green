import time
import unittest



class TestResultStates(unittest.TestCase):


    def test_pass(self):
        return


    def test_error(self):
        raise Exception


    def test_fail(self):
        self.assertTrue(False)



class TestOutputBeforeAndAfter(unittest.TestCase):


    def setUp(self):
        time.sleep(0.7)


    def test_simplePass(self):
        return


    def test_simpleError(self):
        raise Exception


    def test_simpleFail(self):
        self.assertTrue(False)
