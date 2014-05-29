from __future__ import unicode_literals
import unittest

from green.runner import GreenTestRunner
from green.output import GreenStream

try:
    from io import StringIO
except:
    from StringIO import StringIO



class TestGreenTestRunner(unittest.TestCase):


    def setUp(self):
        self.stream = StringIO()


    def tearDown(self):
        del(self.stream)


    def test_instantiate(self):
        "GreenTestRunner can be instantiated and creates a default stream."
        gtr = GreenTestRunner()
        self.assertTrue(type(gtr.stream), GreenStream)


    def test_HTML(self):
        "html=True causes html output"
        class FakeCase(unittest.TestCase):
            def runTest(self):
                pass
        gtr = GreenTestRunner(self.stream, html=True, subprocesses=1)
        gtr.run(FakeCase())
        self.assertIn('<', self.stream.getvalue())


    def test_verbose3(self):
        "verbose=3 causes version output, and an empty test case passes."
        class FakeCase(unittest.TestCase):
            def runTest(self):
                pass
        gtr = GreenTestRunner(self.stream, verbosity=3, subprocesses=1)
        gtr.run(FakeCase())
        self.assertTrue('Green' in self.stream.getvalue())
        self.assertTrue('OK' in self.stream.getvalue())


    def test_warnings(self):
        "setting warnings='always' doesn't crash"
        class FakeCase(unittest.TestCase):
            def runTest(self):
                pass
        gtr = GreenTestRunner(self.stream, warnings='always', subprocesses=1)
        gtr.run(FakeCase())


    def test_noTestsFound(self):
        "When we don't find any tests, we say so."
        gtr = GreenTestRunner(self.stream, subprocesses=1)
        gtr.run(unittest.TestSuite())
        self.assertTrue('No Tests Found' in self.stream.getvalue())


    def test_failedSaysSo(self):
        "A failing test case causes the whole run to report 'FAILED'"
        class FailCase(unittest.TestCase):
            def runTest(self):
                self.assertTrue(False)
        gtr = GreenTestRunner(self.stream, subprocesses=1)
        gtr.run(FailCase())
        self.assertTrue('FAILED' in self.stream.getvalue())
