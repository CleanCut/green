from __future__ import unicode_literals

from xml.etree.ElementTree import Element, SubElement, tostring as to_xml



class JUnitDialect(object):
    """
    Hold the name of the elements defined in the JUnit XML schema.
    """
    FAILURE = "failure"
    NAME = "name"
    TEST_CASE = "testcase"
    TEST_SUITE = "testsuite"
    TEST_SUITES = "testsuites"



class Verdict(object):
    PASSED=0
    FAILED=1
    ERROR=2
    SKIPPED=3



class JUnitXML(object):
    """
    Serialize a GreenTestResult object into a JUnit XML file, that can
    be read by CI.
    """


    def save_as(self, test_results, destination):
        xml_root = Element(JUnitDialect.TEST_SUITES)
        tests_by_class = self._group_tests_by_class(test_results)
        for key, each_suite in tests_by_class.items():
            xml_suite = SubElement(xml_root, JUnitDialect.TEST_SUITE)
            xml_suite.set(JUnitDialect.NAME, key)
            for each_test in each_suite:
                xml_test = self._convert_to_xml(*each_test)
                xml_suite.append(xml_test)
        destination.write(to_xml(xml_root, method="xml").decode())


    def _group_tests_by_class(self, test_results):
        result = {}
        for each_test in test_results.passing:
            key = "%s.%s" % (each_test.module, each_test.class_name)
            if key not in result:
                result[key] = []
            result[key].append((Verdict.PASSED, each_test))
        for each_test, error in test_results.failures:
            key = "%s.%s" % (each_test.module, each_test.class_name)
            if key not in result:
                result[key] = []
            result[key].append((Verdict.FAILED, each_test, error))
        return result


    def _convert_to_xml(self, verdict, test, *details):
        xml_test = Element(JUnitDialect.TEST_CASE)
        xml_test.set(JUnitDialect.NAME, test.method_name)
        if verdict == Verdict.FAILED:
            failure = SubElement(xml_test, JUnitDialect.FAILURE)
            failure.text = str(details[0])
        return xml_test
