from nose.plugins import PluginTester
import unittest
try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock

from green.plugin import Green



class TestPlugin(PluginTester, unittest.TestCase):

    def setUp(self):
        self.g = Green()


    def test_NOSE_GREEN_setsEnabled(self):
        parser = MagicMock()
        self.assertEqual(self.g.enabled, False)
        self.g.options(parser, env={'NOSE_GREEN':'1'})
        self.assertEqual(self.g.enabled, True)



