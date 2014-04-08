from nose.plugins import PluginTester
import unittest
#try:
#    from unittest.mock import MagicMock
#except:
#    from mock import MagicMock

from green.plugin import DevNull, Green



class TestDevNull(unittest.TestCase):


    def test_write(self):
        d = DevNull()
        d.write("YOU SHOULD NOT SEE THIS #1")


    def test_writeln(self):
        d = DevNull()
        d.writeln("YOU SHOULD NOT SEE THIS #2")



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
        self.assertIn('someTest', self.output)




