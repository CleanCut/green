from __future__ import unicode_literals

from lxml.etree import Element, SubElement, tostring as to_xml


class JUnitDialect(object):
    """
    Hold the name of the elements defined in the JUnit XML schema (for JUnit 4).
    """

    CLASS_NAME = "classname"
    ERROR = "error"
    ERROR_COUNT = "errors"
    FAILURE = "failure"
    FAILURE_COUNT = "failures"
    NAME = "name"
    SKIPPED = "skipped"
    SKIPPED_COUNT = "skipped"
    SYSTEM_ERR = "system-err"
    SYSTEM_OUT = "system-out"
    TEST_CASE = "testcase"
    TEST_COUNT = "tests"
    TEST_SUITE = "testsuite"
    TEST_SUITES = "testsuites"
    TEST_TIME = "time"


class Verdict(object):
    """
    Enumeration of possible test verdicts
    """

    PASSED = 0
    FAILED = 1
    ERROR = 2
    SKIPPED = 3


class JUnitXML(object):
    """
    Serialize a GreenTestResult object into a JUnit XML file, that can
    be read by continuous integration servers, for example.

    See GitHub Issue #104
    See Option '-j' / '--junit-report'
    """

    def save_as(self, test_results, destination):
        xml_root = Element(JUnitDialect.TEST_SUITES)
        tests_by_class = self._group_tests_by_class(test_results)
        for name, suite in tests_by_class.items():
            xml_suite = self._convert_suite(test_results, name, suite)
            xml_root.append(xml_suite)

        xml_root.set(JUnitDialect.TEST_TIME, str(test_results.timeTaken))

        xml = to_xml(
            xml_root,
            xml_declaration=True,
            pretty_print=True,
            encoding="utf-8",
            method="xml",
        )
        destination.write(xml.decode())

    def _group_tests_by_class(self, test_results):
        result = {}
        self._add_passing_tests(result, test_results)
        self._add_failures(result, test_results)
        self._add_errors(result, test_results)
        self._add_skipped_tests(result, test_results)
        return result

    @staticmethod
    def _add_passing_tests(collection, test_results):
        for each_test in test_results.passing:
            key = JUnitXML._suite_name(each_test)
            if key not in collection:
                collection[key] = []
            collection[key].append((Verdict.PASSED, each_test))

    @staticmethod
    def _suite_name(test):
        return "%s.%s" % (test.module, test.class_name)

    @staticmethod
    def _add_failures(collection, test_results):
        for each_test, failure in test_results.failures:
            key = JUnitXML._suite_name(each_test)
            if key not in collection:
                collection[key] = []
            collection[key].append((Verdict.FAILED, each_test, failure))

    @staticmethod
    def _add_errors(collection, test_results):
        for each_test, error in test_results.errors:
            key = JUnitXML._suite_name(each_test)
            if key not in collection:
                collection[key] = []
            collection[key].append((Verdict.ERROR, each_test, error))

    @staticmethod
    def _add_skipped_tests(collection, test_results):
        for each_test, reason in test_results.skipped:
            key = JUnitXML._suite_name(each_test)
            if key not in collection:
                collection[key] = []
            collection[key].append((Verdict.SKIPPED, each_test, reason))

    def _convert_suite(self, results, name, suite):
        xml_suite = Element(JUnitDialect.TEST_SUITE)
        xml_suite.set(JUnitDialect.NAME, name)
        xml_suite.set(JUnitDialect.TEST_COUNT, str(len(suite)))
        xml_suite.set(
            JUnitDialect.FAILURE_COUNT,
            str(self._count_test_with_verdict(Verdict.FAILED, suite)),
        )
        xml_suite.set(
            JUnitDialect.ERROR_COUNT,
            str(self._count_test_with_verdict(Verdict.ERROR, suite)),
        )
        xml_suite.set(
            JUnitDialect.SKIPPED_COUNT,
            str(self._count_test_with_verdict(Verdict.SKIPPED, suite)),
        )
        xml_suite.set(JUnitDialect.TEST_TIME, str(self._suite_time(suite)))
        for each_test in suite:
            xml_test = self._convert_test(results, *each_test)
            xml_suite.append(xml_test)

        return xml_suite

    @staticmethod
    def _count_test_with_verdict(verdict, suite):
        return sum(1 for entry in suite if entry[0] == verdict)

    def _convert_test(self, results, verdict, test, *details):
        xml_test = Element(JUnitDialect.TEST_CASE)
        xml_test.set(JUnitDialect.NAME, test.method_name)
        xml_test.set(JUnitDialect.CLASS_NAME, test.class_name)
        xml_test.set(JUnitDialect.TEST_TIME, test.test_time)

        xml_verdict = self._convert_verdict(verdict, test, details)
        if verdict:
            xml_test.append(xml_verdict)

        if test in results.stdout_output:
            system_out = Element(JUnitDialect.SYSTEM_OUT)
            system_out.text = results.stdout_output[test]
            xml_test.append(system_out)

        if test in results.stderr_errput:
            system_err = Element(JUnitDialect.SYSTEM_ERR)
            system_err.text = results.stderr_errput[test]
            xml_test.append(system_err)

        return xml_test

    def _convert_verdict(self, verdict, test, details):
        if verdict == Verdict.FAILED:
            failure = Element(JUnitDialect.FAILURE)
            failure.text = str(details[0])
            return failure
        if verdict == Verdict.ERROR:
            error = Element(JUnitDialect.ERROR)
            error.text = str(details[0])
            return error
        if verdict == Verdict.SKIPPED:
            skipped = Element(JUnitDialect.SKIPPED)
            skipped.text = str(details[0])
            return skipped
        return None

    @staticmethod
    def _suite_time(suite):
        return sum(float(each_test.test_time) for verdict, each_test, *details in suite)
