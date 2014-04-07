from nose.plugins import PluginTester
import unittest
#try:
#    from unittest.mock import MagicMock
#except:
#    from mock import MagicMock

from green.plugin import Green



class TestPlugin(PluginTester, unittest.TestCase):
    activate = '--with-green'
    plugins = [Green()]


    def makeSuite(self):
        class SampleTestCase(unittest.TestCase):
            def someTest(self):
                pass
        return [SampleTestCase('someTest')]


    def test_GreenInformation(self):
        self.assertIn('Green', self.output)


    def test_NoseInformation(self):
        self.assertIn('Nose', self.output)


    def test_PythonInformation(self):
        self.assertIn('Python', self.output)


    def test_modulePrintout(self):
        self.assertIn('test_plugin', self.output)




