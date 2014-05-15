from __future__ import unicode_literals
import sys
import unittest

from green.runner import GreenTestResult, GreenTestRunner
from green.output import GreenStream

try:
    from io import StringIO
except:
    from StringIO import StringIO

try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock



class TestGreenTestResult(unittest.TestCase):


    def setUp(self):
        self.stream = StringIO()


    def tearDown(self):
        del(self.stream)


    def test_startTestVerbose(self):
        "startTest() contains output we expect in verbose mode"
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
        "_reportOutcome contains output we expect"
        gtr = GreenTestResult(GreenStream(self.stream), None, 1)
        gtr._reportOutcome(None, '.', lambda x: x)
        self.assertTrue('.' in self.stream.getvalue())


    def test_reportOutcomeVerbose(self):
        "_reportOutcome contains output we expect in verbose mode"
        gtr = GreenTestResult(GreenStream(self.stream), None, 2)
        l = 'a fake test output line'
        r = 'a fake reason'
        gtr.test_output_line = l
        gtr._reportOutcome(None, '.', lambda x: x, None, r)
        self.assertTrue(l in self.stream.getvalue())
        self.assertTrue(r in self.stream.getvalue())



class TestGreenTestResultAdds(unittest.TestCase):


    def setUp(self):
        self.stream = StringIO()
        self.gtr = GreenTestResult(GreenStream(self.stream), None, 0)
        self.gtr._reportOutcome = MagicMock()


    def tearDown(self):
        del(self.stream)
        del(self.gtr)


    def test_addSuccess(self):
        "addSuccess() makes the correct calls to other functions."
        test = 'success test'
        self.gtr.addSuccess(test)
        self.gtr._reportOutcome.assert_called_with(
                test, '.', self.gtr.colors.passing)


    def test_addError(self):
        "addError() makes the correct calls to other functions."
        err = None
        try:
            raise Exception
        except:
            err = sys.exc_info()
        test = MagicMock()
        self.gtr.addError(test, err)
        self.gtr._reportOutcome.assert_called_with(
                test, 'E', self.gtr.colors.error, err)


    def test_addFailure(self):
        "addFailure() makes the correct calls to other functions."
        err = None
        try:
            raise Exception
        except:
            err = sys.exc_info()
        test = MagicMock()
        self.gtr.addFailure(test, err)
        self.gtr._reportOutcome.assert_called_with(
                test, 'F', self.gtr.colors.failing, err)


    def test_addSkip(self):
        "addSkip() makes the correct calls to other functions."
        test = 'skip test'
        reason = 'skip reason'
        self.gtr.addSkip(test, reason)
        self.gtr._reportOutcome.assert_called_with(
                test, 's', self.gtr.colors.skipped, reason)


    def test_addExpectedFailure(self):
        "addExpectedFailure() makes the correct calls to other functions."
        try:
            raise Exception
        except:
            err = sys.exc_info()
        test = MagicMock()
        self.gtr.addExpectedFailure(test, err)
        self.gtr._reportOutcome.assert_called_with(
                test, 'x', self.gtr.colors.expectedFailure, err)


    def test_addUnexpectedSuccess(self):
        "addUnexpectedSuccess() makes the correct calls to other functions."
        test = 'unexpected success test'
        self.gtr.addUnexpectedSuccess(test)
        self.gtr._reportOutcome.assert_called_with(
                test, 'u', self.gtr.colors.unexpectedSuccess)



class TestGreenTestRunner(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_instantiate(self):
        "GreenTestRunner can be instantiated"
        GreenTestRunner()
