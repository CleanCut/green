from __future__ import unicode_literals

from green.config import default_args
from green.output import GreenStream
from green.reporting import JUnitXML, JUnitDialect
from green.result import GreenTestResult, ProtoTest, proto_error

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
                "my_method": {"verdict": "PASS"}
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
                "my_method": {"verdict": "FAILED"}
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
        for each_node in test:
            if each_node.tag == JUnitDialect.FAILURE:
                self.assertEqual("FAILED", expected_test["verdict"])
                test_passed = False
            elif each_node.tag == JUnitDialect.ERROR:
                self.assertEqual("ERROR", expected_test["verdict"])
                test_passed = False
            elif each_node.tag == JUnitDialect.SKIPPED:
                self.assertEqual("SKIPPED", expected_test["verdict"])
                test_passed = False

        if test_passed:
            self.assertEqual("PASS", expected_test["verdict"])
