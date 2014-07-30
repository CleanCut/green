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



class MyProtoTest(ProtoTest):
    """
    For quickly making a ProtoTest
    """
    def __init__(self):
        self.module      = "my_module"
        self.class_name  = "MyClass"
        self.method_name = "myMethod"
        self.docstr_part = "My docstring"



class TestProtoTestResult(unittest.TestCase):


    def test_addSuccess(self):
        """
        addSuccess adds a test correctly
        """
        ptr = ProtoTestResult()
        test = proto_test(MagicMock())
        ptr.addSuccess(test)
        self.assertEqual(test, ptr.passing[0])


    def test_addError(self):
        """
        addError adds a test and error correctly
        """
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
        """
        addFailure adds a test and error correctly
        """
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
        """
        addSkip adds a test and reason correctly
        """
        ptr = ProtoTestResult()
        test = proto_test(MagicMock())
        reason = "some plausible reason"
        ptr.addSkip(test, reason)
        self.assertEqual(test, ptr.skipped[0][0])
        self.assertEqual(reason, ptr.skipped[0][1])


    def test_addExpectedFailure(self):
        """
        addExpectedFailure adds a test and error correctly
        """
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
        """
        addUnexpectedSuccess adds a test correctly
        """
        ptr = ProtoTestResult()
        test = proto_test(MagicMock())
        ptr.addUnexpectedSuccess(test)
        self.assertEqual(test, ptr.unexpectedSuccesses[0])



class TestProtoTest(unittest.TestCase):


    def test_ProtoTestBlank(self):
        """
        ProtoTest can be instantiated empty
        """
        pt = ProtoTest()
        for i in ['module', 'class_name', 'docstr_part', 'method_name']:
            self.assertEqual('', getattr(pt, i, None))


    def test_ProtoTestFromTest(self):
        """
        Passing a test into ProtoTest copies out the relevant info.
        """
        module      = 'green.test.test_result'
        class_name  = 'Small'
        docstr_part = 'stuff'
        method_name = 'test_method'

        class Small(unittest.TestCase):
            def test_method(self):
                "stuff"
        pt = ProtoTest(Small('test_method'))

        for i in ['module', 'class_name', 'docstr_part', 'method_name']:
            self.assertEqual(locals()[i], getattr(pt, i, None))


    def test_getDescription(self):
        """
        getDescription() returns what we expect for all verbosity levels
        """
        # With a docstring
        class Fruit(unittest.TestCase):
            def test_stuff(self):
                'apple'
                pass
        t = proto_test(Fruit('test_stuff'))
        self.assertEqual(t.getDescription(1), '')
        self.assertEqual(t.getDescription(2), 'test_stuff')
        self.assertEqual(t.getDescription(3), 'apple')
        self.assertEqual(t.getDescription(4), 'apple')

        # Without a docstring
        class Vegetable(unittest.TestCase):
            def test_stuff(self):
                pass
        t = proto_test(Vegetable('test_stuff'))
        self.assertEqual(t.getDescription(1), '')
        self.assertEqual(t.getDescription(2), 'test_stuff')
        self.assertEqual(t.getDescription(3), 'test_stuff')
        self.assertEqual(t.getDescription(4), 'test_stuff')


    def test_newlineDocstring(self):
        """
        Docstrings starting with a newline are properly handled.
        """
        class MyTests(unittest.TestCase):
            def test_stuff(self):
                """
                tricky
                """
                pass
        test = proto_test(MyTests('test_stuff'))
        self.assertIn('tricky', test.getDescription(3))


    def test_multilineDocstring(self):
        """
        The description includes all of docstring until the first blank line.
        """
        class LongDocs(unittest.TestCase):
            def test_long(self):
                """First line is
                tricky!

                garbage
                """
                pass
        test = proto_test(LongDocs('test_long'))
        self.assertIn('tricky', test.getDescription(3))
        self.assertNotIn('garbage', test.getDescription(3))



class TestGreenTestResult(unittest.TestCase):


    def setUp(self):
        self.stream = StringIO()


    def tearDown(self):
        del(self.stream)


    def test_startTestVerbose(self):
        """
        startTest() contains output we expect in verbose mode
        """
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
        self.assertNotIn(' ', output_lines[0])
        self.assertIn('  ', output_lines[1])
        self.assertIn('    ', output_lines[2])


    def test_reportOutcome(self):
        """
        _reportOutcome contains output we expect
        """
        gtr = GreenTestResult(GreenStream(self.stream), None, 1)
        gtr._reportOutcome(None, '.', lambda x: x)
        self.assertIn('.', self.stream.getvalue())


    def test_reportOutcomeVerbose(self):
        """
        _reportOutcome contains output we expect in verbose mode
        """
        gtr = GreenTestResult(GreenStream(self.stream), None, 2)
        r = 'a fake reason'
        t = MagicMock()
        t.__str__.return_value = 'junk'
        gtr._reportOutcome(t, '.', lambda x: x, None, r)
        self.assertIn(r, self.stream.getvalue())


    def test_reportOutcomeVerboseHTML(self):
        """
        html=True causes _reportOutcome() to escape HTML in docstrings
        """
        gtr = GreenTestResult(GreenStream(self.stream), None, 3)
        gtr.colors.html = True
        r = 'a fake reason'
        class Injection(unittest.TestCase):
            def test_method(self):
                'a fake test output line &nbsp; <>'
        t = proto_test(Injection('test_method'))
        gtr._reportOutcome(t, '.', lambda x: x, None, r)
        self.assertTrue(r in self.stream.getvalue())
        self.assertTrue('&amp;' in self.stream.getvalue())
        self.assertTrue('&lt;' in self.stream.getvalue())
        self.assertTrue('&gt;' in self.stream.getvalue())
        self.assertFalse('&nbsp;' in self.stream.getvalue())
        self.assertFalse('<' in self.stream.getvalue())
        self.assertFalse('>' in self.stream.getvalue())


    def test_printErrorsDots(self):
        """
        printErrors() looks correct in verbose=1 (dots) mode
        """
        try:
            raise Exception
        except:
            err = sys.exc_info()
        gtr = GreenTestResult(GreenStream(self.stream), None, 1, False, False)
        gtr.addError(MyProtoTest(), proto_error(err))
        gtr.printErrors()
        self.assertIn('\n\n', self.stream.getvalue())
        self.assertIn('my_module.MyClass.myMethod', self.stream.getvalue())
        self.assertIn('test_printErrorsDots', self.stream.getvalue())
        self.assertIn('raise Exception', self.stream.getvalue())
        self.assertIn('Error', self.stream.getvalue())


    def test_printErrorsVerbose2(self):
        """
        printErrors() looks correct in verbose=2 mode
        """
        try:
            raise Exception
        except:
            err = sys.exc_info()
        gtr = GreenTestResult(GreenStream(self.stream), None, 2, False, False)
        gtr.addError(MyProtoTest(), proto_error(err))
        gtr.printErrors()
        self.assertIn('\n\n', self.stream.getvalue())
        self.assertIn('my_module.MyClass.myMethod', self.stream.getvalue())
        self.assertIn('test_printErrorsVerbose2', self.stream.getvalue())
        self.assertIn('raise Exception', self.stream.getvalue())
        self.assertIn('Error', self.stream.getvalue())


    def test_printErrorsVerbose3(self):
        """
        printErrors() looks correct in verbose=3 mode
        """
        try:
            raise Exception
        except:
            err = sys.exc_info()
        gtr = GreenTestResult(GreenStream(self.stream), None, 3, False, False)
        gtr.addError(MyProtoTest(), proto_error(err))
        gtr.printErrors()
        self.assertIn('\n\n', self.stream.getvalue())
        self.assertIn('my_module.MyClass.myMethod', self.stream.getvalue())
        self.assertIn('test_printErrorsVerbose3', self.stream.getvalue())
        self.assertIn('raise Exception', self.stream.getvalue())
        self.assertIn('Error', self.stream.getvalue())


    def test_printErrorsVerbose4(self):
        """
        printErrors() looks correct in verbose=4 mode
        """
        try:
            raise Exception
        except:
            err = sys.exc_info()
        gtr = GreenTestResult(GreenStream(self.stream), None, 4, False, False)
        gtr.addError(MyProtoTest(), err)
        gtr.printErrors()
        self.assertIn('\n\n', self.stream.getvalue())
        self.assertIn('(most recent call last)', self.stream.getvalue())
        self.assertIn('my_module.MyClass.myMethod', self.stream.getvalue())
        self.assertIn('test_printErrorsVerbose4', self.stream.getvalue())
        self.assertIn('raise Exception', self.stream.getvalue())
        self.assertIn('Error', self.stream.getvalue())


    def test_printErrorsZHTML(self):
        """
        printErrors() looks correct in html mode
        """
        try:
            raise Exception
        except:
            err = sys.exc_info()
        gtr = GreenTestResult(GreenStream(self.stream), None, 4)
        gtr.colors.html = True
        test = MagicMock()
        gtr.addError(test, proto_error(err))
        gtr.printErrors()
        self.assertIn('\n\n', self.stream.getvalue())
        self.assertIn('(most recent call last)', self.stream.getvalue())
        self.assertIn('test_printErrorsZHTML', self.stream.getvalue())
        self.assertIn('raise Exception', self.stream.getvalue())
        self.assertIn('Error', self.stream.getvalue())
        self.assertIn('<span', self.stream.getvalue())
        self.assertIn('color: rgb(', self.stream.getvalue())


    def test_addProtoTestResult(self):
        """
        addProtoTestResult adds the correct things to the correct places
        """
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
        """
        addSuccess() makes the correct calls to other functions.
        """
        test = MagicMock()
        test.shortDescription.return_value = 'a'
        test.__str__.return_value = 'b'
        test = proto_test(test)
        self.gtr.addSuccess(test)
        self.gtr._reportOutcome.assert_called_with(
                test, '.', self.gtr.colors.passing)


    def test_addError(self):
        """
        addError() makes the correct calls to other functions.
        """
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
        """
        addFailure() makes the correct calls to other functions.
        """
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
        """
        addSkip() makes the correct calls to other functions.
        """
        test = proto_test(MagicMock())
        reason = 'skip reason'
        self.gtr.addSkip(test, reason)
        self.gtr._reportOutcome.assert_called_with(
                test, 's', self.gtr.colors.skipped, reason=reason)


    def test_addExpectedFailure(self):
        """
        addExpectedFailure() makes the correct calls to other functions.
        """
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
        """
        addUnexpectedSuccess() makes the correct calls to other functions.
        """
        test = proto_test(MagicMock())
        self.gtr.addUnexpectedSuccess(test)
        self.gtr._reportOutcome.assert_called_with(
                test, 'u', self.gtr.colors.unexpectedSuccess)


    def test_wasSuccessful(self):
        "wasSuccessful returns what we expect"
        gtr = GreenTestResult(GreenStream(self.stream), None, 1)
        self.assertEqual(gtr.wasSuccessful(), True)
        gtr.all_errors.append('anything')
        self.assertEqual(gtr.wasSuccessful(), False)
