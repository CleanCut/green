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


    def test_startTestVerbose(self):
        gtr = GreenTestResult(GreenStream(self.stream), None, 2)
        class FakeCase(unittest.TestCase):
            def test_it(self):
                pass
        tc = FakeCase('test_it')
        gtr.startTest(tc)
        output = self.stream.getvalue()
        output_lines = output.split('\n')
        # Output should look like (I'm not putting the termcolor formatting here)
        # green.test.test_runner
        #   FakeCase
        #     test_it
        self.assertEqual(len(output_lines), 3)
        self.assertFalse(' ' in output_lines[0])
        self.assertTrue('  ' in output_lines[1])
        self.assertTrue('    ' in output_lines[2])


    def test_reportOutcome(self):
        gtr = GreenTestResult(GreenStream(self.stream), None, 1)
        gtr._reportOutcome(None, '.', lambda x: x)
        self.assertTrue('.' in self.stream.getvalue())


    def test_reportOutcomeVerbose(self):
        gtr = GreenTestResult(GreenStream(self.stream), None, 2)
        l = 'a fake test output line'
        r = 'a fake reason'
        gtr.test_output_line = l
        gtr._reportOutcome(None, '.', lambda x: x, None, r)
        self.assertTrue(l in self.stream.getvalue())
        self.assertTrue(r in self.stream.getvalue())


    def test_addResultTypes(self):
        gtr = GreenTestResult(GreenStream(self.stream), None, 2)


class TestGreenTestRunner(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_instantiate(self):
        GreenTestRunner()
