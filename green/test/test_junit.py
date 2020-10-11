from __future__ import unicode_literals

from green.config import default_args
from green.output import GreenStream
from green.junit import JUnitXML, JUnitDialect, Verdict
from green.result import GreenTestResult, BaseTestResult, ProtoTest, proto_error

from io import StringIO

from sys import exc_info

from unittest import TestCase

from xml.etree.ElementTree import fromstring as from_xml, tostring as to_xml


def test(module, class_name, method_name):
    test = ProtoTest()
    test.module = module
    test.class_name = class_name
    test.method_name = method_name
    return test


class JUnitXMLReportIsGenerated(TestCase):
    def setUp(self):
        self._destination = StringIO()
        self._test_results = GreenTestResult(default_args, GreenStream(StringIO()))
        self._test_results.timeTaken = 4.06
        self._adapter = JUnitXML()

        self._test = ProtoTest()
        self._test.module = "my_module"
        self._test.class_name = "MyClass"
        self._test.method_name = "my_method"
        self._test.test_time = "0.005"

    def test_when_the_results_contain_only_one_successful_test(self):
        self._test_results.addSuccess(self._test)

        self._adapter.save_as(self._test_results, self._destination)

        self._assert_report_is(
            {"my_module.MyClass": {"tests": {"my_method": {"verdict": Verdict.PASSED}}}}
        )

    def test_when_the_results_contain_tests_with_various_verdict(self):
        self._test_results.addSuccess(test("my.module", "MyClass", "test_method1"))
        self._test_results.addSuccess(test("my.module", "MyClass", "test_method2"))
        self._record_failure(test("my.module", "MyClass", "test_method3"))
        self._record_failure(test("my.module", "MyClass", "test_method4"))
        self._record_error(test("my.module", "MyClass", "test_method5"))
        self._test_results.addSkip(
            test("my.module", "MyClass", "test_method6"), "Take too long"
        )

        self._adapter.save_as(self._test_results, self._destination)

        self._assert_report_is(
            {
                "my.module.MyClass": {
                    "#tests": "6",
                    "#failures": "2",
                    "#errors": "1",
                    "#skipped": "1",
                    "tests": {
                        "test_method1": {"verdict": Verdict.PASSED},
                        "test_method2": {"verdict": Verdict.PASSED},
                        "test_method3": {"verdict": Verdict.FAILED},
                        "test_method4": {"verdict": Verdict.FAILED},
                        "test_method5": {"verdict": Verdict.ERROR},
                        "test_method6": {"verdict": Verdict.SKIPPED},
                    },
                },
            }
        )

    def _record_failure(self, test):
        try:
            raise ValueError("Wrong value")
        except:
            error = proto_error(exc_info())
        self._test_results.addFailure(test, error)

    def _record_error(self, test):
        try:
            raise ValueError("Wrong value")
        except:
            error = proto_error(exc_info())
        self._test_results.addError(test, error)

    def test_when_the_results_contain_only_one_test_with_output(self):
        output = "This is the output of the test"
        self._test_results.recordStdout(self._test, output)
        self._test_results.addSuccess(self._test)

        self._adapter.save_as(self._test_results, self._destination)

        self._assert_report_is(
            {
                "my_module.MyClass": {
                    "tests": {
                        "my_method": {"verdict": Verdict.PASSED, "stdout": output}
                    }
                }
            }
        )

    def test_when_the_results_contain_only_one_test_with_errput(self):
        errput = "This is the errput of the test"
        self._test_results.recordStderr(self._test, errput)
        self._test_results.addSuccess(self._test)

        self._adapter.save_as(self._test_results, self._destination)

        self._assert_report_is(
            {
                "my_module.MyClass": {
                    "tests": {
                        "my_method": {"verdict": Verdict.PASSED, "stderr": errput}
                    }
                }
            }
        )

    def test_when_the_results_contain_only_one_failed_test(self):
        self._record_failure(test("my_module", "MyClass", "my_method"))

        self._adapter.save_as(self._test_results, self._destination)

        self._assert_report_is(
            {"my_module.MyClass": {"tests": {"my_method": {"verdict": Verdict.FAILED}}}}
        )

    def test_when_the_results_contain_only_one_erroneous_test(self):
        self._record_error(test("my_module", "MyClass", "my_method"))

        self._adapter.save_as(self._test_results, self._destination)

        self._assert_report_is(
            {"my_module.MyClass": {"tests": {"my_method": {"verdict": Verdict.ERROR}}}}
        )

    def test_when_the_results_contain_only_one_skipped_test(self):
        self._test_results.addSkip(self._test, "reason for skipping")

        self._adapter.save_as(self._test_results, self._destination)

        self._assert_report_is(
            {
                "my_module.MyClass": {
                    "tests": {"my_method": {"verdict": Verdict.SKIPPED}}
                }
            }
        )

    def test_convert_test_will_record_time_for_test(self):
        xml_test_result = self._adapter._convert_test(
            self._test_results, Verdict.PASSED, self._test
        )

        self.assertEqual(
            xml_test_result.attrib,
            {"name": "my_method", "classname": "MyClass", "time": "0.005"},
        )

    def test_suite_time(self):
        test1 = test("my.module", "MyClass", "test_method1")
        test1.test_time = "0.01"
        test2 = test("my.module", "MyClass", "test_method2")
        test2.test_time = "0.5"
        test3 = test("my.module", "MyClass", "test_method3")
        test3.test_time = "1.0"

        suite_time = self._adapter._suite_time([(2, test1), (0, test2), (0, test3)])

        self.assertEqual(suite_time, 1.51)

    def _assert_report_is(self, report):
        """
        Verify the structure of the generated XML text against the given
        'report' structure.
        """
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

        # Check the count of tests
        if "#tests" in expected_suite:
            self.assertEqual(
                expected_suite["#tests"], suite.get(JUnitDialect.TEST_COUNT)
            )

        # Check the count of failures
        if "#failures" in expected_suite:
            self.assertEqual(
                expected_suite["#failures"], suite.get(JUnitDialect.FAILURE_COUNT)
            )

        # Check the count of errors
        if "#errors" in expected_suite:
            self.assertEqual(
                expected_suite["#errors"], suite.get(JUnitDialect.ERROR_COUNT)
            )

        # Check the count of skipped tests
        if "#skipped" in expected_suite:
            self.assertEqual(
                expected_suite["#skipped"], suite.get(JUnitDialect.SKIPPED_COUNT)
            )

        # Check the time of each test
        if "time" in expected_suite:
            self.assertEqual(expected_suite["time"], suite.get(JUnitDialect.TEST_TIME))

        # Check the time of total test run
        if "totaltesttime" in expected_suite:
            self.assertEqual(
                expected_suite["totaltesttime"], suite.get(JUnitDialect.TEST_TIME)
            )

        # Check individual test reports
        self.assertEqual(len(expected_suite["tests"]), len(suite))
        for each_test in suite:
            self._assert_test(expected_suite["tests"], each_test)

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

        else:  # Verdict == PASSED
            self.assertIsNone(failure)
            self.assertIsNone(error)
            self.assertIsNone(skipped)
