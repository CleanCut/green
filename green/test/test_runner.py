from __future__ import unicode_literals
import unittest

from green.runner import GreenTestResult, GreenTestRunner

try:
    from io import StringIO
except:
    from StringIO import StringIO



class TestGreenTestResult(unittest.TestCase):


    def setUp(self):
        self.stream = StringIO


    def tearDown(self):
        del(self.stream)


    def test_instantiate(self):
        gtr = GreenTestResult(None, None, 0)
