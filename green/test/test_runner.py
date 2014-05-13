from __future__ import unicode_literals
import unittest

from green.runner import GreenTestResult, GreenTestRunner
from green.output import GreenStream

try:
    from io import StringIO
except:
    from StringIO import StringIO



class TestGreenTestResult(unittest.TestCase):


    def setUp(self):
        self.stream = StringIO()


    def tearDown(self):
        del(self.stream)


    def test_instantiate(self):
        GreenTestResult(None, None, 0)


    def test_startTestVerboseEmpty(self):
        gtr = GreenTestResult(GreenStream(self.stream), None, 2)
        tc = unittest.TestCase()
        gtr.startTest(tc)
        output = self.stream.getvalue()
        output_lines = output.split('\n')
        # Output should look like (I'm not putting the termcolor formatting here)
        # unittest.case
        #   TestCase
        #     No test
        self.assertEqual(len(output_lines), 3)
        self.assertFalse(' ' in output_lines[0])
        self.assertTrue('  ' in output_lines[1])
        self.assertTrue('    ' in output_lines[2])



class TestGreenTestRunner(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_instantiate(self):
        GreenTestRunner()
