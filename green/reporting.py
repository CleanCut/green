from __future__ import unicode_literals

from lxml.etree import Element, SubElement, tostring as to_xml



class JUnitDialect(object):
    """
    Hold the name of the elements defined in the JUnit XML schema.
    """
    CLASS_NAME = "classname"
    ERROR = "error"
    FAILURE = "failure"
    NAME = "name"
    SKIPPED = "skipped"
    TEST_CASE = "testcase"
    TEST_SUITE = "testsuite"
    TEST_SUITES = "testsuites"



class Verdict(object):
    """
    Enumeration of possible test verdicts
    """
    PASSED=0
    FAILED=1
    ERROR=2
    SKIPPED=3



class JUnitXML(object):
    """
    Serialize a GreenTestResult object into a JUnit XML file, that can
    be read by continuous integration servers, for example.
    """

    def save_as(self, test_results, destination):
        xml_root = Element(JUnitDialect.TEST_SUITES)
        tests_by_class = self._group_tests_by_class(test_results)
        for name, suite in tests_by_class.items():
            xml_suite = self._convert_suite(name, suite)
            xml_root.append(xml_suite)
        xml = to_xml(xml_root,
                     xml_declaration=True,
                     pretty_print=True,
                     encoding="utf-8",
                     method="xml")
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


    def _convert_suite(self, name, suite):
        xml_suite = Element(JUnitDialect.TEST_SUITE)
        xml_suite.set(JUnitDialect.NAME, name)
        for each_test in suite:
            xml_test = self._convert_test(*each_test)
            xml_suite.append(xml_test)
        return xml_suite


    def _convert_test(self, verdict, test, *details):
        xml_test = Element(JUnitDialect.TEST_CASE)
        xml_test.set(JUnitDialect.NAME, test.method_name)
        xml_test.set(JUnitDialect.CLASS_NAME, test.class_name)
        if verdict == Verdict.FAILED:
            failure = SubElement(xml_test, JUnitDialect.FAILURE)
            failure.text = str(details[0])
        elif verdict == Verdict.ERROR:
            error = SubElement(xml_test, JUnitDialect.ERROR)
            error.text = str(details[0])
        elif verdict == Verdict.SKIPPED:
            skipped = SubElement(xml_test, JUnitDialect.SKIPPED)
            skipped.text = str(details[0])
        return xml_test
