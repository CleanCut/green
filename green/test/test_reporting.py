from __future__ import unicode_literals

from green.config import default_args
from green.output import GreenStream
from green.reporting import JUnitXML, JUnitDialect, Verdict
from green.result import GreenTestResult, BaseTestResult, ProtoTest, proto_error

from io import StringIO

from sys import exc_info

from unittest import TestCase

from xml.etree.ElementTree import fromstring as from_xml, tostring as to_xml



class JUnitXMLReportIsGenerated(TestCase):


    def setUp(self):
        self._destination = StringIO()
        self._test_results = GreenTestResult(default_args,
                                             GreenStream(StringIO()))
        self._adapter = JUnitXML()

        self._test = ProtoTest()
        self._test.module      = "my_module"
        self._test.class_name  = "MyClass"
        self._test.method_name = "my_method"



    def test_when_the_results_contain_only_one_successful_test(self):
        self._test_results.addSuccess(self._test)

        self._adapter.save_as(self._test_results, self._destination)

        self._assert_report_is({
            "my_module.MyClass": {
                "my_method": {"verdict": Verdict.PASSED}
            }
        })


    def test_when_the_results_contain_only_one_test_with_output(self):
        output = "This is the output of the test"
        self._test_results.recordStdout(self._test, output)
        self._test_results.addSuccess(self._test)

        self._adapter.save_as(self._test_results, self._destination)

        self._assert_report_is({
            "my_module.MyClass": {
                "my_method": {
                    "verdict": Verdict.PASSED,
                    "stdout": output
                }
            }
        })


    def test_when_the_results_contain_only_one_test_with_errput(self):
        errput = "This is the errput of the test"
        self._test_results.recordStderr(self._test, errput)
        self._test_results.addSuccess(self._test)

        self._adapter.save_as(self._test_results, self._destination)

        self._assert_report_is({
            "my_module.MyClass": {
                "my_method": {
                    "verdict": Verdict.PASSED,
                    "stderr": errput
                }
            }
        })



    def test_when_the_results_contain_only_one_failed_test(self):
        try:
            raise Exception
        except:
            error = proto_error(exc_info())
        self._test_results.addFailure(self._test, error)

        self._adapter.save_as(self._test_results, self._destination)

        self._assert_report_is({
            "my_module.MyClass": {
                "my_method": {"verdict": Verdict.FAILED}
            }
        })


    def test_when_the_results_contain_only_one_erroneous_test(self):
        try:
            raise Exception
        except:
            error = proto_error(exc_info())
        self._test_results.addError(self._test, error)

        self._adapter.save_as(self._test_results, self._destination)

        self._assert_report_is({
            "my_module.MyClass": {
                "my_method": {"verdict": Verdict.ERROR}
            }
        })


    def test_when_the_results_contain_only_one_skipped_test(self):
        self._test_results.addSkip(self._test, "reason for skipping")

        self._adapter.save_as(self._test_results, self._destination)

        self._assert_report_is({
            "my_module.MyClass": {
                "my_method": {"verdict": Verdict.SKIPPED}
            }
        })



    def _assert_report_is(self, report):
        """
        Verify the structure of the generated XML text against the given
        'report' structure.
        """
        print(self._destination.getvalue())
        root = from_xml(self._destination.getvalue())
        test_suites = root.findall(JUnitDialect.TEST_SUITE)
        self.assertEqual(len(report), len(test_suites))
        for each_suite in test_suites:
            self._assert_suite(report, each_suite)


    def _assert_suite(self, expected_report, suite):
        """
        Verify that the given 'suite' matches one in the expected test report.
        """
        name = suite.get(JUnitDialect.NAME)
        self.assertIsNotNone(name)
        self.assertIn(name, expected_report)
        expected_suite = expected_report[name]
        self.assertEqual(len(expected_suite), len(suite))
        for each_test in suite:
            self._assert_test(expected_suite, each_test)


    def _assert_test(self, expected_suite, test):
        """
        Verify that the given 'test' matches one in the expected test suite.
        """
        name = test.get(JUnitDialect.NAME)
        self.assertIsNotNone(test)
        self.assertIn(name, expected_suite)
        expected_test = expected_suite[name]

        test_passed = True

        for key, expected in expected_test.items():
            if key == "verdict":
                self._assert_verdict(expected, test)

            elif key == "stdout":
                system_out = test.find(JUnitDialect.SYSTEM_OUT)
                self.assertIsNotNone(system_out)
                self.assertEqual(expected, system_out.text)

            elif key == "stderr":
                system_err = test.find(JUnitDialect.SYSTEM_ERR)
                self.assertIsNotNone(system_err)
                self.assertEqual(expected, system_err.text)



    def _assert_verdict(self, expected_verdict, test):
        failure = test.find(JUnitDialect.FAILURE)
        error = test.find(JUnitDialect.ERROR)
        skipped = test.find(JUnitDialect.SKIPPED)

        if expected_verdict == Verdict.FAILED:
            self.assertIsNotNone(failure)
            self.assertIsNone(error)
            self.assertIsNone(skipped)

        elif expected_verdict == Verdict.ERROR:
            self.assertIsNone(failure)
            self.assertIsNotNone(error)
            self.assertIsNone(skipped)


        elif expected_verdict == Verdict.SKIPPED:
            self.assertIsNone(failure)
            self.assertIsNone(error)
            self.assertIsNotNone(skipped)

        else: # Verdict == PASSED
            self.assertIsNone(failure)
            self.assertIsNone(error)
            self.assertIsNone(skipped)
