from __future__ import unicode_literals
import sys
import unittest

from green.output import GreenStream
from green.result import GreenTestResult, proto_test, \
        ProtoTest, proto_error, ProtoTestResult

try:
    from io import StringIO
except:
    from StringIO import StringIO

try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock


class TestProtoTestResult(unittest.TestCase):


    def test_addSuccess(self):
        "addSuccess adds a test correctly"
        ptr = ProtoTestResult()
        test = proto_test(MagicMock())
        ptr.addSuccess(test)
        self.assertEqual(test, ptr.passing[0])


    def test_addError(self):
        "addError adds a test and error correctly"
        ptr = ProtoTestResult()
        test = proto_test(MagicMock())
        try:
            raise Exception
        except:
            err = proto_error(sys.exc_info())
        ptr.addError(test, err)
        self.assertEqual(test, ptr.errors[0][0])
        self.assertEqual(err, ptr.errors[0][1])


    def test_addFailure(self):
        "addFailure adds a test and error correctly"
        ptr = ProtoTestResult()
        test = proto_test(MagicMock())
        try:
            raise Exception
        except:
            err = proto_error(sys.exc_info())
        ptr.addFailure(test, err)
        self.assertEqual(test, ptr.failures[0][0])
        self.assertEqual(err, ptr.failures[0][1])


    def test_addSkip(self):
        "addSkip adds a test and reason correctly"
        ptr = ProtoTestResult()
        test = proto_test(MagicMock())
        reason = "some plausible reason"
        ptr.addSkip(test, reason)
        self.assertEqual(test, ptr.skipped[0][0])
        self.assertEqual(reason, ptr.skipped[0][1])


    def test_addExpectedFailure(self):
        "addExpectedFailure adds a test and error correctly"
        ptr = ProtoTestResult()
        test = proto_test(MagicMock())
        try:
            raise Exception
        except:
            err = proto_error(sys.exc_info())
        ptr.addExpectedFailure(test, err)
        self.assertEqual(test, ptr.expectedFailures[0][0])
        self.assertEqual(err, ptr.expectedFailures[0][1])


    def test_addUnexpectedSuccess(self):
        "addUnexpectedSuccess adds a test correctly"
        ptr = ProtoTestResult()
        test = proto_test(MagicMock())
        ptr.addUnexpectedSuccess(test)
        self.assertEqual(test, ptr.unexpectedSuccesses[0])



class TestProtoTest(unittest.TestCase):


    def test_ProtoTestBlank(self):
        "ProtoTest can be instantiated empty"
        pt = ProtoTest()
        for i in ['module', 'class_name', 'description', 'method_name']:
            self.assertEqual('', getattr(pt, i, None))


    def test_ProtoTestFromTest(self):
        "Passing a test into ProtoTest copies out the relevant info."
        module      = 'some_module'
        class_name  = 'some_class'
        description = 'stuff'
        method_name = 'method()'

        t             = MagicMock()
        t.__module__  = module
        t.__class__.__name__  = str(class_name)
        t.shortDescription.return_value = description
        t.__str__.return_value = method_name

        pt = ProtoTest(t)

        for i in ['module', 'class_name', 'description', 'method_name']:
            self.assertEqual(locals()[i], getattr(pt, i, None))



class TestGreenTestResult(unittest.TestCase):


    def setUp(self):
        self.stream = StringIO()


    def tearDown(self):
        del(self.stream)


    def test_startTestVerbose(self):
        "startTest() contains output we expect in verbose mode"
        class FakeCase(unittest.TestCase):
            def runTest(self):
                pass
        gtr = GreenTestResult(GreenStream(self.stream), None, 2)
        tc = FakeCase()
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


    def test_reportOutcomeVerboseHTML(self):
        "html=True causes _reportOutcome() to escape HTML in docstrings"
        gtr = GreenTestResult(GreenStream(self.stream), None, 2)
        gtr.colors.html = True
        l = 'a fake test output line &nbsp; <>'
        r = 'a fake reason'
        gtr.test_output_line = l
        gtr._reportOutcome(None, '.', lambda x: x, None, r)
        self.assertTrue(r in self.stream.getvalue())
        self.assertTrue('&amp;' in self.stream.getvalue())
        self.assertTrue('&lt;' in self.stream.getvalue())
        self.assertTrue('&gt;' in self.stream.getvalue())
        self.assertFalse('&nbsp;' in self.stream.getvalue())
        self.assertFalse('<' in self.stream.getvalue())
        self.assertFalse('>' in self.stream.getvalue())


    def test_printErrorsDots(self):
        "printErrors() looks correct in verbose=1 (dots) mode"
        try:
            raise Exception
        except:
            err = sys.exc_info()
        gtr = GreenTestResult(GreenStream(self.stream), None, 1)
        test = MagicMock()
        gtr.addError(test, proto_error(err))
        gtr.printErrors()
        self.assertTrue('\n\n' in self.stream.getvalue())
        self.assertTrue('test_printErrorsDots' in self.stream.getvalue())
        self.assertTrue('raise Exception' in self.stream.getvalue())
        self.assertTrue('Error' in self.stream.getvalue())


    def test_printErrorsVerbose2(self):
        "printErrors() looks correct in verbose=2 mode"
        try:
            raise Exception
        except:
            err = sys.exc_info()
        gtr = GreenTestResult(GreenStream(self.stream), None, 2)
        gtr.test_output_line = "   some test output"
        test = MagicMock()
        gtr.addError(test, proto_error(err))
        gtr.printErrors()
        self.assertTrue('\n\n' in self.stream.getvalue())
        self.assertTrue('test_printErrorsVerbose2' in self.stream.getvalue())
        self.assertTrue('raise Exception' in self.stream.getvalue())
        self.assertTrue('Error' in self.stream.getvalue())


    def test_printErrorsVerbose4(self):
        "printErrors() looks correct in verbose=4 mode"
        try:
            raise Exception
        except:
            err = sys.exc_info()
        gtr = GreenTestResult(GreenStream(self.stream), None, 4)
        gtr.test_output_line = "   some test output"
        test = MagicMock()
        gtr.addError(test, err)
        gtr.printErrors()
        self.assertTrue('\n\n' in self.stream.getvalue())
        self.assertTrue('(most recent call last)' in self.stream.getvalue())
        self.assertTrue('test_printErrorsVerbose4' in self.stream.getvalue())
        self.assertTrue('raise Exception' in self.stream.getvalue())
        self.assertTrue('Error' in self.stream.getvalue())


    def test_printErrorsZHTML(self):
        "printErrors() looks correct in html mode"
        try:
            raise Exception
        except:
            err = sys.exc_info()
        gtr = GreenTestResult(GreenStream(self.stream), None, 4)
        gtr.colors.html = True
        gtr.test_output_line = "   some test output"
        test = MagicMock()
        gtr.addError(test, proto_error(err))
        gtr.printErrors()
        self.assertTrue('\n\n' in self.stream.getvalue())
        self.assertTrue('(most recent call last)' in self.stream.getvalue())
        self.assertTrue('test_printErrorsZHTML' in self.stream.getvalue())
        self.assertTrue('raise Exception' in self.stream.getvalue())
        self.assertTrue('Error' in self.stream.getvalue())
        self.assertTrue('<span' in self.stream.getvalue())
        self.assertTrue('color: rgb(' in self.stream.getvalue())


    def test_addProtoTestResult(self):
        "addProtoTestResult adds the correct things to the correct places"
        ptr = ProtoTestResult()

        err_t = proto_test(MagicMock())
        try:
            raise Exception
        except:
            err_e = proto_error(sys.exc_info())
        ptr.addError(err_t, err_e)

        ef_t = proto_test(MagicMock())
        try:
            raise Exception
        except:
            ef_e = proto_error(sys.exc_info())
        ptr.addExpectedFailure(ef_t, ef_e)

        fail_t = proto_test(MagicMock())
        try:
            raise Exception
        except:
            fail_e = proto_error(sys.exc_info())
        ptr.addFailure(fail_t, fail_e)

        pass_t = proto_test(MagicMock())
        ptr.addSuccess(pass_t)

        skip_t = proto_test(MagicMock())
        skip_r = proto_test(MagicMock())
        ptr.addSkip(skip_t, skip_r)

        us_t = proto_test(MagicMock())
        ptr.addUnexpectedSuccess(us_t)

        gtr = GreenTestResult(GreenStream(self.stream), None, 0)
        gtr.addProtoTestResult(ptr)

        self.assertEqual(gtr.errors, [(err_t, err_e)])
        self.assertEqual(gtr.expectedFailures, [(ef_t, ef_e)])
        self.assertEqual(gtr.failures, [(fail_t, fail_e)])
        self.assertEqual(gtr.passing, [pass_t])
        self.assertEqual(gtr.skipped, [(skip_t, skip_r)])
        self.assertEqual(gtr.unexpectedSuccesses, [us_t])



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
        try:
            raise Exception
        except:
            err = sys.exc_info()
        test = proto_test(MagicMock())
        err = proto_error(err)
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
        test = proto_test(MagicMock())
        err = proto_error(err)
        self.gtr.addFailure(test, err)
        self.gtr._reportOutcome.assert_called_with(
                test, 'F', self.gtr.colors.failing, err)


    def test_addSkip(self):
        "addSkip() makes the correct calls to other functions."
        test = 'skip test'
        reason = 'skip reason'
        self.gtr.addSkip(test, reason)
        self.gtr._reportOutcome.assert_called_with(
                test, 's', self.gtr.colors.skipped, reason=reason)


    def test_addExpectedFailure(self):
        "addExpectedFailure() makes the correct calls to other functions."
        try:
            raise Exception
        except:
            err = sys.exc_info()
        test = proto_test(MagicMock())
        err = proto_error(err)
        self.gtr.addExpectedFailure(test, err)
        self.gtr._reportOutcome.assert_called_with(
                test, 'x', self.gtr.colors.expectedFailure, err)


    def test_addUnexpectedSuccess(self):
        "addUnexpectedSuccess() makes the correct calls to other functions."
        test = 'unexpected success test'
        self.gtr.addUnexpectedSuccess(test)
        self.gtr._reportOutcome.assert_called_with(
                test, 'u', self.gtr.colors.unexpectedSuccess)
