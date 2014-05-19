from __future__ import unicode_literals
import sys
import unittest

from green import cmdline
from green.output import GreenStream

try:
    from io import StringIO
except:
    from StringIO import StringIO



class TestMain(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_optVersion(self):
        "--version causes a version string to be output"
        s = StringIO()
        g = GreenStream(s)
        saved_stdout = sys.stdout
        saved_argv = sys.argv
        sys.stdout = g
        cmdline.sys.argv = ['', '--version']
        cmdline.main()
        sys.stdout = saved_stdout
        sys.argv = saved_argv

