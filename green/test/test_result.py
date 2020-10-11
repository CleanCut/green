# encoding: utf-8
from __future__ import unicode_literals
import copy

# `from doctest import DocTestCase` causes crashes, since the DocTestCase is
# detected as a TestCase subclass and unittest.TestLoader.loadTestsFromModule()
# called from GreenTestLoader.loadTestsFromModule() thinks it is a definition
# of a test to actually try to run, and causes very weird crashes.
import doctest
from io import StringIO
import sys
import os
import unittest
import tempfile

from green.config import default_args
from green.output import Colors, GreenStream
from green.result import (
    GreenTestResult,
    proto_test,
    ProtoTest,
    proto_error,
    ProtoTestResult,
    BaseTestResult,
)

try:
    from unittest.mock import MagicMock, patch
except ImportError:
    from mock import MagicMock, patch

from coverage import coverage, CoverageException


class MyProtoTest(ProtoTest, object):
    """
    For quickly making a ProtoTest
    """

    def __init__(self):
        super(MyProtoTest, self).__init__()
        self.module = "my_module"
        self.class_name = "MyClass"
        self.method_name = "myMethod"
        self.docstr_part = "My docstring"
        self.subtest_part = ""


class TestBaseTestResult(unittest.TestCase):
    def test_stdoutOutput(self):
        """
        recordStdout records output.
        """
        btr = BaseTestResult(None, None)
        pt = ProtoTest()
        o = "some output"
        btr.recordStdout(pt, o)
        self.assertEqual(btr.stdout_output[pt], o)

    def test_stdoutNoOutput(self):
        """
        recordStdout ignores empty output sent to it
        """
        btr = BaseTestResult(None, None)
        pt = ProtoTest()
        btr.recordStdout(pt, "")
        self.assertEqual(btr.stdout_output, {})

    def test_displayStdout(self):
        """
        displayStdout displays captured stdout
        """
        stream = StringIO()
        noise = "blah blah blah"
        btr = BaseTestResult(stream, Colors(False))
        pt = ProtoTest()
        btr.stdout_output[pt] = noise
        btr.displayStdout(pt)
        self.assertIn(noise, stream.getvalue())

    def test_stderrErrput(self):
        """
        recordStderr records errput.
        """
        btr = BaseTestResult(None, None)
        pt = ProtoTest()
        o = "some errput"
        btr.recordStderr(pt, o)
        self.assertEqual(btr.stderr_errput[pt], o)

    def test_stderrNoErrput(self):
        """
        recordStderr ignores empty errput sent to it
        """
        btr = BaseTestResult(None, None)
        pt = ProtoTest()
        btr.recordStderr(pt, "")
        self.assertEqual(btr.stderr_errput, {})

    def test_displayStderr(self):
        """
        displayStderr displays captured stderr
        """
        stream = StringIO()
        noise = "blah blah blah"
        btr = BaseTestResult(stream, Colors(False))
        pt = ProtoTest()
        btr.stderr_errput[pt] = noise
        btr.displayStderr(pt)
        self.assertIn(noise, stream.getvalue())


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

    @patch("green.result.ProtoTestResult.addError")
    @patch("green.result.ProtoTestResult.addFailure")
    def test_addSubTest_failure(self, mock_addFailure, mock_addError):
        """
        addSubTest calls over to addFailure for failures
        """
        ptr = ProtoTestResult()
        test = proto_test(MagicMock())
        test.failureException = Exception
        subtest = MagicMock()
        err = [Exception]
        ptr.addSubTest(test, subtest, err)
        mock_addFailure.assert_called_with(subtest, err)

    @patch("green.result.ProtoTestResult.addError")
    @patch("green.result.ProtoTestResult.addFailure")
    def test_addSubTest_error(self, mock_addFailure, mock_addError):
        """
        addSubTest calls over to addError for errors
        """
        ptr = ProtoTestResult()
        test = proto_test(MagicMock())
        test.failureException = KeyError
        subtest = MagicMock()
        err = [Exception]
        ptr.addSubTest(test, subtest, err)
        mock_addError.assert_called_with(subtest, err)


class TestProtoError(unittest.TestCase):
    def test_str(self):
        """
        Running a ProtoError through str() should result in a traceback string
        """
        test_str = "noetuaoe"
        try:
            raise Exception(test_str)
        except:
            err = sys.exc_info()
        pe = proto_error(err)
        self.assertIn(test_str, str(pe))


class TestProtoTest(unittest.TestCase):
    def test_ProtoTestBlank(self):
        """
        ProtoTest can be instantiated empty
        """
        pt = ProtoTest()
        for i in ["module", "class_name", "docstr_part", "method_name"]:
            self.assertEqual("", getattr(pt, i, None))

    def test_str(self):
        """
        Running a ProtoTest through str() is the same as getting .dotted_name
        """
        pt = ProtoTest()
        pt.module = "aoeusnth"
        self.assertEqual(str(pt), pt.dotted_name)

    def test_ProtoTestFromTest(self):
        """
        Passing a test into ProtoTest copies out the relevant info.
        """
        module = "green.test.test_result"
        class_name = "Small"
        docstr_part = "stuff"
        method_name = "test_method"

        class Small(unittest.TestCase):
            def test_method(self):
                "stuff"

        pt = ProtoTest(Small("test_method"))

        for i in ["module", "class_name", "docstr_part", "method_name"]:
            self.assertEqual(locals()[i], getattr(pt, i, None))

    def test_getDescription(self):
        """
        getDescription() returns what we expect for all verbose levels
        """
        # With a docstring
        class Fruit(unittest.TestCase):
            def test_stuff(self):
                "apple"
                pass

        t = proto_test(Fruit("test_stuff"))
        self.assertEqual(t.getDescription(1), "")
        self.assertEqual(t.getDescription(2), "test_stuff")
        self.assertEqual(t.getDescription(3), "apple")
        self.assertEqual(t.getDescription(4), "apple")

        # Without a docstring
        class Vegetable(unittest.TestCase):
            def test_stuff(self):
                pass

        t = proto_test(Vegetable("test_stuff"))
        self.assertEqual(t.getDescription(1), "")
        self.assertEqual(t.getDescription(2), "test_stuff")
        self.assertEqual(t.getDescription(3), "test_stuff")
        self.assertEqual(t.getDescription(4), "test_stuff")

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

        test = proto_test(MyTests("test_stuff"))
        self.assertIn("tricky", test.getDescription(3))

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

        test = proto_test(LongDocs("test_long"))
        self.assertIn("tricky", test.getDescription(3))
        self.assertNotIn("garbage", test.getDescription(3))

    def test_doctest(self):
        """
        If we parse a doctest, we get all the fields we need.
        """
        test = """
        >>> f()
        42
        """

        def f():
            return 42

        parser = doctest.DocTestParser()
        dt = parser.get_doctest(test, {"f": f}, "doctest.name", "somefile.py", 20)
        dt.__module__ = "somefile"
        p = proto_test(doctest.DocTestCase(dt))
        # short description
        self.assertEqual(p.getDescription(2), "doctest.name")
        # long description
        description = p.getDescription(3)
        self.assertIn("doctest.name", description)
        self.assertIn("somefile.py", description)
        self.assertIn("20", description)
        # dotted name
        self.assertEqual(p.dotted_name, "doctest.name")

    def test_class_or_module_failure(self):
        """
        If we parse an error from a class or module failure, we get the correct result.
        """
        p = ProtoTest()
        p.is_class_or_module_teardown_error = True
        p.name = "the thing"
        self.assertEqual(p.getDescription(1), "the thing")
        self.assertEqual(p.getDescription(2), "the thing")
        self.assertEqual(p.getDescription(3), "the thing")


class TestGreenTestResult(unittest.TestCase):
    def setUp(self):
        self.args = copy.deepcopy(default_args)
        self.stream = StringIO()

    def tearDown(self):
        del self.stream
        del self.args

    @patch("green.result.GreenTestResult.printErrors")
    def test_stopTestRun(self, mock_printErrors):
        """
        We ignore coverage's error about not having anything to cover.
        """
        self.args.cov = MagicMock()
        self.args.cov.stop = MagicMock(
            side_effect=CoverageException("Different Exception")
        )
        self.args.run_coverage = True
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.startTestRun()
        self.assertRaises(CoverageException, gtr.stopTestRun)

        self.args.cov.stop = MagicMock(
            side_effect=CoverageException("No data to report")
        )

    def test_tryRecordingStdoutStderr(self):
        """
        Recording stdout and stderr works correctly.
        """
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.recordStdout = MagicMock()
        gtr.recordStderr = MagicMock()

        output = "apple"
        test1 = MagicMock()
        ptr1 = MagicMock()
        ptr1.stdout_output = {test1: output}
        ptr1.stderr_errput = {}

        errput = "banana"
        test2 = MagicMock()
        ptr2 = MagicMock()
        ptr2.stdout_output = {}
        ptr2.stderr_errput = {test2: errput}

        gtr.tryRecordingStdoutStderr(test1, ptr1)
        gtr.recordStdout.assert_called_with(test1, output)
        gtr.tryRecordingStdoutStderr(test2, ptr2)
        gtr.recordStderr.assert_called_with(test2, errput)

    def test_failfastAddError(self):
        """
        addError triggers failfast when it is set
        """
        self.args.failfast = True
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        self.assertEqual(gtr.failfast, True)
        try:
            raise Exception
        except:
            err = sys.exc_info()
        self.assertEqual(gtr.shouldStop, False)
        gtr.addError(MyProtoTest(), proto_error(err))
        self.assertEqual(gtr.shouldStop, True)

    def test_failfastAddFailure(self):
        """
        addFailure triggers failfast when it is set
        """
        self.args.failfast = True
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        self.assertEqual(gtr.failfast, True)
        try:
            raise Exception
        except:
            err = sys.exc_info()
        self.assertEqual(gtr.shouldStop, False)
        gtr.addFailure(MyProtoTest(), proto_error(err))
        self.assertEqual(gtr.shouldStop, True)

    def test_failfastAddUnexpectedSuccess(self):
        """
        addUnexpectedSuccess no longer triggers failfast when it is set
        """
        self.args.failfast = True
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        self.assertEqual(gtr.failfast, True)
        self.assertEqual(gtr.shouldStop, False)
        gtr.addUnexpectedSuccess(MyProtoTest())
        self.assertEqual(gtr.shouldStop, False)

    def _outputFromVerboseTest(self):
        """
        Start a test with verbose = 2 and get its output.
        """

        class FakeCase(unittest.TestCase):
            def runTest(self):
                pass

        self.args.verbose = 2
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        tc = FakeCase()
        gtr.startTest(tc)
        output = self.stream.getvalue()
        return output.split("\n")

    def test_startTestVerboseTerminal(self):
        """
        startTest() contains output we expect in verbose mode on a terminal
        """
        self.stream.isatty = lambda: True
        output_lines = self._outputFromVerboseTest()
        # Output should look like (I'm not putting the termcolor formatting
        # here)
        # green.test.test_runner
        #   FakeCase
        #     test_it
        self.assertEqual(len(output_lines), 3)
        self.assertNotIn(" ", output_lines[0])
        self.assertIn("  ", output_lines[1])
        self.assertIn("    ", output_lines[2])

    def test_startTestVerbosePipe(self):
        """
        startTest() contains output we expect in verbose mode on a pipe
        """
        self.stream.isatty = lambda: False
        output_lines = self._outputFromVerboseTest()
        # Output should look like (I'm not putting the termcolor formatting
        # here)
        # green.test.test_runner
        #   FakeCase
        #     test_it
        self.assertEqual(len(output_lines), 3)
        self.assertNotIn(" ", output_lines[0])
        self.assertIn("  ", output_lines[1])
        # No carriage return or extra lines printed
        self.assertIn("", output_lines[2])

    def test_reportOutcome(self):
        """
        _reportOutcome contains output we expect.
        """
        self.args.verbose = 1
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr._reportOutcome(None, ".", lambda x: x)
        self.assertIn(".", self.stream.getvalue())

    @patch("green.result.proto_test")
    def test_reportOutcomeCursorUp(self, mock_proto_test):
        """
        _reportOutcome moves the cursor up when it needs to.
        """
        mockProtoTest = MagicMock()
        mockProtoTest.getDescription.return_value = "a description"
        mock_proto_test.return_value = mockProtoTest
        self.args.verbose = 2

        def isatty():
            return True

        gs = GreenStream(self.stream)
        gs.isatty = isatty
        gtr = GreenTestResult(self.args, gs)
        r = "a fake reason"
        t = MagicMock()
        t.__str__.return_value = "x" * 1000
        gtr._reportOutcome(t, ".", lambda x: x, None, r)
        self.assertIn(r, self.stream.getvalue())
        self.assertLess(len(self.stream.getvalue()), 2000)

    @patch("green.result.proto_test")
    def test_reportOutcomeVerbose(self, mock_proto_test):
        """
        _reportOutcome contains output we expect in verbose mode.
        """
        mockProtoTest = MagicMock()
        mockProtoTest.getDescription.return_value = "a description"
        mock_proto_test.return_value = mockProtoTest
        self.args.verbose = 2

        def isatty():
            return True

        gs = GreenStream(self.stream)
        gs.isatty = isatty
        gtr = GreenTestResult(self.args, gs)
        r = "a fake reason"
        t = MagicMock()
        t.__str__.return_value = "junk"
        gtr._reportOutcome(t, ".", lambda x: x, None, r)
        self.assertIn(r, self.stream.getvalue())

    def test_printErrorsSkipreport(self):
        """
        printErrors() prints the skip report.
        """
        self.args.verbose = 1
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        pt = MyProtoTest()
        reason = "dog ate homework"
        gtr.addSkip(pt, reason)
        gtr.printErrors()
        self.assertIn(reason, self.stream.getvalue())

    def test_printErrorsStdout(self):
        """
        printErrors() prints out the captured stdout.
        """
        self.args.verbose = 1
        self.args.termcolor = False
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        pt = MyProtoTest()
        output = "this is what the test spit out to stdout"
        gtr.recordStdout(pt, output)
        gtr.addSuccess(pt)
        gtr.printErrors()
        self.assertIn(output, self.stream.getvalue())

    def test_printErrorsStdoutQuietStdoutOnSuccess(self):
        """
        printErrors() prints out the captured stdout
        except when quiet_stdout is set to True
        for successful tests.
        """
        self.args.quiet_stdout = True
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        pt = MyProtoTest()
        output = "this is what the test should not spit out to stdout"
        gtr.recordStdout(pt, output)
        gtr.addSuccess(pt)
        gtr.printErrors()
        self.assertNotIn(output, self.stream.getvalue())

    def test_printErrorsStdoutQuietStdoutOnError(self):
        """
        printErrors() prints out the captured stdout
        except when quiet_stdout is set to True
        for successful tests, but here we are on a
        failing test.
        """
        self.args.quiet_stdout = True
        try:
            raise Exception
        except:
            err = sys.exc_info()
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        pt = MyProtoTest()
        output = "this is what the test should spit out to stdout"
        gtr.recordStdout(pt, output)
        gtr.addError(pt, proto_error(err))
        gtr.printErrors()
        self.assertIn(output, self.stream.getvalue())

    def test_printErrorsStderrQuietStdoutOnSuccess(self):
        """
        printErrors() prints out the captured stdout
        except when quiet_stdout is set to True
        for successful tests.
        """
        self.args.quiet_stdout = True
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        pt = MyProtoTest()
        output = "this is what the test should not spit out to stdout"
        gtr.recordStderr(pt, output)
        gtr.addSuccess(pt)
        gtr.printErrors()
        self.assertNotIn(output, self.stream.getvalue())

    def test_printErrorsNoTracebacks(self):
        """
        printErrors() omits tracebacks for failures and errors when
        no_tracebacks is True
        """
        self.args.no_tracebacks = True
        try:
            raise Exception
        except:
            err = sys.exc_info()
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        pt = MyProtoTest()
        gtr.addError(pt, proto_error(err))
        gtr.printErrors()
        self.assertNotIn("Exception", self.stream.getvalue())

    def test_printErrorsDots(self):
        """
        printErrors() looks correct in verbose=1 (dots) mode.
        """
        try:
            raise Exception
        except:
            err = sys.exc_info()
        self.args.verbose = 1
        self.args.termcolor = False
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.addError(MyProtoTest(), proto_error(err))
        gtr.printErrors()
        self.assertIn("\n\n", self.stream.getvalue())
        self.assertIn("my_module.MyClass.myMethod", self.stream.getvalue())
        self.assertIn("test_printErrorsDots", self.stream.getvalue())
        self.assertIn("raise Exception", self.stream.getvalue())
        self.assertIn("Error", self.stream.getvalue())

    def test_printErrorsVerbose2(self):
        """
        printErrors() looks correct in verbose=2 mode.
        """
        try:
            raise Exception
        except:
            err = sys.exc_info()
        self.args.verbose = 2
        self.args.termcolor = False
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.addError(MyProtoTest(), proto_error(err))
        gtr.printErrors()
        self.assertIn("\n\n", self.stream.getvalue())
        self.assertIn("my_module.MyClass.myMethod", self.stream.getvalue())
        self.assertIn("test_printErrorsVerbose2", self.stream.getvalue())
        self.assertIn("raise Exception", self.stream.getvalue())
        self.assertIn("Error", self.stream.getvalue())

    def test_printErrorsVerbose3(self):
        """
        printErrors() looks correct in verbose=3 mode.
        """
        try:
            raise Exception
        except:
            err = sys.exc_info()
        self.args.verbose = 3
        self.args.termcolor = False
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.addError(MyProtoTest(), proto_error(err))
        gtr.printErrors()
        self.assertIn("\n\n", self.stream.getvalue())
        self.assertIn("my_module.MyClass.myMethod", self.stream.getvalue())
        self.assertIn("test_printErrorsVerbose3", self.stream.getvalue())
        self.assertIn("raise Exception", self.stream.getvalue())
        self.assertIn("Error", self.stream.getvalue())

    def test_printErrorsVerbose4(self):
        """
        printErrors() looks correct in verbose=4 mode.
        """
        try:
            raise Exception
        except:
            err = sys.exc_info()
        self.args.verbose = 4
        self.args.termcolor = False
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.addError(MyProtoTest(), err)
        gtr.printErrors()
        self.assertIn("\n\n", self.stream.getvalue())
        self.assertIn("(most recent call last)", self.stream.getvalue())
        self.assertIn("my_module.MyClass.myMethod", self.stream.getvalue())
        self.assertIn("test_printErrorsVerbose4", self.stream.getvalue())
        self.assertIn("raise Exception", self.stream.getvalue())
        self.assertIn("Error", self.stream.getvalue())

    def test_printErrors_Py2Unicode(self):
        """
        printErrors() doesn't crash in Python 2 when tracebacks contain unicode
        """
        try:
            raise Exception("Das Böse ist immer und überall")
        except:
            err = sys.exc_info()
        self.args.verbose = 1
        self.args.termcolor = False
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.addError(MyProtoTest(), proto_error(err))
        gtr.printErrors()  # We shouldn't hit an exception here
        self.assertIn("\n\n", self.stream.getvalue())
        self.assertIn("my_module.MyClass.myMethod", self.stream.getvalue())
        self.assertIn("raise Exception", self.stream.getvalue())
        self.assertIn("Error", self.stream.getvalue())
        self.assertIn("Böse", self.stream.getvalue())

    def test_addProtoTestResult(self):
        """
        addProtoTestResult adds the correct things to the correct places.
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

        self.args.verbose = 0
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.addProtoTestResult(ptr)

        self.assertEqual(gtr.errors, [(err_t, err_e)])
        self.assertEqual(gtr.expectedFailures, [(ef_t, ef_e)])
        self.assertEqual(gtr.failures, [(fail_t, fail_e)])
        self.assertEqual(gtr.passing, [pass_t])
        self.assertEqual(gtr.skipped, [(skip_t, skip_r)])
        self.assertEqual(gtr.unexpectedSuccesses, [us_t])

    def test_stopTestRun_processes_message(self):
        """
        StopTestRun adds number of processes used to summary
        """
        self.args.processes = 4
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.startTestRun()
        gtr.stopTestRun()

        self.assertIn("using 4 processes\n", self.stream.getvalue())

    def test_stopTestRun_singular_process_message(self):
        """
        StopTestRun adds correct summary when one process is used
        """
        self.args.processes = 1
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.startTestRun()
        gtr.stopTestRun()

        self.assertIn("using 1 process\n", self.stream.getvalue())


class TestGreenTestResultAdds(unittest.TestCase):
    def setUp(self):
        self.stream = StringIO()
        self.args = copy.deepcopy(default_args)
        self.args.verbose = 0
        self.gtr = GreenTestResult(self.args, GreenStream(self.stream))
        self.gtr._reportOutcome = MagicMock()

    def tearDown(self):
        del self.stream
        del self.gtr

    def test_addSuccess(self):
        """
        addSuccess() makes the correct calls to other functions.
        """
        test = MagicMock()
        test.shortDescription.return_value = "a"
        test.__str__.return_value = "b"
        test = proto_test(test)
        self.gtr.addSuccess(test)
        self.gtr._reportOutcome.assert_called_with(test, ".", self.gtr.colors.passing)

    def test_addSuccess_with_test_time(self):
        """
        addSuccess() sets test time to correct value
        """
        test = MagicMock()
        test.shortDescription.return_value = "a"
        test.__str__.return_value = "b"
        test = proto_test(test)
        self.gtr.addSuccess(test, "0.42")

        self.assertEqual(test.test_time, "0.42")

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
            test, "E", self.gtr.colors.error, err
        )

    def test_addError_with_test_time(self):
        """
        addError() sets test time to correct value
        """
        try:
            raise Exception
        except:
            err = sys.exc_info()
        test = proto_test(MagicMock())
        err = proto_error(err)
        self.gtr.addError(test, err, "0.42")

        self.assertEqual(test.test_time, "0.42")

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
            test, "F", self.gtr.colors.failing, err
        )

    def test_addFailure_with_test_time(self):
        """
        addFailure() makes test time the correct value
        """
        err = None
        try:
            raise Exception
        except:
            err = sys.exc_info()
        test = proto_test(MagicMock())
        err = proto_error(err)
        self.gtr.addFailure(test, err, "0.42")

        self.assertEqual(test.test_time, "0.42")

    def test_addFailureTwistedSkip(self):
        """
        Twisted's practice of calling addFailure() with their skips is detected
        and redirected to addSkip()
        """
        err = None
        try:
            raise Exception
        except:
            err = sys.exc_info()
        test = proto_test(MagicMock())
        reason = "Twisted is odd"
        err = proto_error(err)
        err.traceback_lines = ["UnsupportedTrialFeature: ('skip', '{}')".format(reason)]
        self.gtr.addFailure(test, err)
        self.gtr._reportOutcome.assert_called_with(
            test, "s", self.gtr.colors.skipped, reason=reason
        )

    def test_addSkip(self):
        """
        addSkip() makes the correct calls to other functions.
        """
        test = proto_test(MagicMock())
        reason = "skip reason"
        self.gtr.addSkip(test, reason)
        self.gtr._reportOutcome.assert_called_with(
            test, "s", self.gtr.colors.skipped, reason=reason
        )

    def test_addSkip_with_test_time(self):
        """
        addSkip() makes test time the correct value
        """
        test = proto_test(MagicMock())
        reason = "skip reason"
        self.gtr.addSkip(test, reason, "0.42")

        self.assertEqual(test.test_time, "0.42")

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
            test, "x", self.gtr.colors.expectedFailure, err
        )

    def test_addExcepectedFailure_with_test_time(self):
        """
        addExpectedFailure() makes test time correct value
        """
        try:
            raise Exception
        except:
            err = sys.exc_info()
        test = proto_test(MagicMock())
        err = proto_error(err)
        self.gtr.addExpectedFailure(test, err, "0.42")

        self.assertEqual(test.test_time, "0.42")

    def test_addUnexpectedSuccess(self):
        """
        addUnexpectedSuccess() makes the correct calls to other functions.
        """
        test = proto_test(MagicMock())
        self.gtr.addUnexpectedSuccess(test)
        self.gtr._reportOutcome.assert_called_with(
            test, "u", self.gtr.colors.unexpectedSuccess
        )

    def test_addUnexpectedSuccess_with_test_time(self):
        """
        addUnexpectedSuccess() makes test time with correct value
        """
        test = proto_test(MagicMock())
        self.gtr.addUnexpectedSuccess(test, "0.42")

        self.assertEqual(test.test_time, "0.42")

    def test_wasSuccessful(self):
        """
        wasSuccessful returns what we expect.
        """
        self.args.verbose = 1
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        self.assertEqual(gtr.wasSuccessful(), False)
        gtr.passing.append("anything")
        self.assertEqual(gtr.wasSuccessful(), True)
        gtr.all_errors.append("anything")
        self.assertEqual(gtr.wasSuccessful(), False)

    def test_wasSuccessful_expectedFailures(self):
        """
        wasSuccessful returns what we expect when we only have expectedFailures
        """
        self.args.verbose = 1
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.expectedFailures.append("anything")
        self.assertEqual(gtr.wasSuccessful(), True)

    def test_wasSuccessful_passing(self):
        """
        wasSuccessful returns what we expect when we only have passing tests
        """
        self.args.verbose = 1
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.passing.append("anything")
        self.assertEqual(gtr.wasSuccessful(), True)

    def test_wasSuccessful_skipped(self):
        """
        wasSuccessful returns what we expect when we only have skipped tests
        """
        self.args.verbose = 1
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.skipped.append("anything")
        self.assertEqual(gtr.wasSuccessful(), True)

    def test_wasSuccessful_unexpectedSuccesses(self):
        """
        wasSuccessful returns what we expect when we only have unexpectedSuccesses
        """
        self.args.verbose = 1
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.unexpectedSuccesses.append("anything")
        self.assertEqual(gtr.wasSuccessful(), True)

    def test_wasSuccessful_coverageFails(self):
        """
        wasSuccessful fails if minimum coverage is not met
        """
        self.args.minimum_coverage = 50
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.coverage_percent = 49
        self.assertEqual(gtr.wasSuccessful(), False)

    def test_wasSuccessful_coverageSucceeds(self):
        """
        wasSuccessful succeds if minimum coverage is met
        """
        self.args.minimum_coverage = 50
        gtr = GreenTestResult(self.args, GreenStream(self.stream))
        gtr.passing.append("anything")
        gtr.coverage_percent = 60
        self.assertEqual(gtr.wasSuccessful(), True)


class TestGreenTestRunCoverage(unittest.TestCase):
    def setUp(self):
        self.args = copy.deepcopy(default_args)

        cov_file = tempfile.NamedTemporaryFile(delete=False)
        cov_file.close()

        self.args.cov = coverage(
            data_file=cov_file.name,
            omit=self.args.omit_patterns,
            include=self.args.include_patterns,
        )
        self.args.cov.start()
        self.stream = StringIO()

    def tearDown(self):
        del self.stream
        del self.args

    def _outputFromTest(self, args):
        class FakeCase(unittest.TestCase):
            def runTest(self):
                pass

        gtr = GreenTestResult(args, GreenStream(self.stream))
        gtr.startTestRun()
        gtr.startTest(FakeCase())
        gtr.stopTestRun()
        output = self.stream.getvalue()
        return output.split("\n")

    def test_coverage(self):
        self.args.run_coverage = True
        output = self._outputFromTest(self.args)
        self.assertIn("Stmts   Miss  Cover   Missing", "\n".join(output))

    def test_quiet_coverage(self):
        self.args.run_coverage = True
        self.args.quiet_coverage = True
        output = self._outputFromTest(self.args)
        self.assertNotIn("Stmts   Miss  Cover   Missing", "\n".join(output))
