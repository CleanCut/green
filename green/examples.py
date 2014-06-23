from __future__ import unicode_literals
import unittest



class TestStates(unittest.TestCase):


    def test0Pass(self):
        "This test will pass"
        return


    def test1Fail(self):
        "This test will fail an assertion"
        self.assertTrue(False)


    def test2Error(self):
        "An Exception will be raised (and not caught) while running this test."
        raise Exception


    @unittest.skip("This is the 'reason' portion of the skipped test.")
    def test3Skip(self):
        "This test will be skipped."
        pass

    @unittest.expectedFailure
    def test4ExpectedFailure(self):
        "This test will fail, but we expect it to."
        self.assertEqual(True, False)


    @unittest.expectedFailure
    def test5UnexpectedPass(self):
        "This test will pass, but we expected it to fail!"
        pass


#    def test6SmallDelay(self):
#        "This test will take 1 seconds to pass."
#        import time
#        time.sleep(1)
#
#
#    def test7BigDelay(self):
#        "This test will take 2 seconds to pass."
#        import time
#        time.sleep(2)
#
#
#    def test8AnotherDelay(self):
#        "This test will also take 2 seconds to pass, but not if you use 3 or more subprocesses!"
#        import time
#        time.sleep(2)
