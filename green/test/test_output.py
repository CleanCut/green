from __future__ import unicode_literals
import sys
import unittest

try:
    from io import StringIO
except:
    from StringIO import StringIO

from green.output import Colors, GreenStream, debug
import green.output



class TestDebug(unittest.TestCase):


    def testDebug(self):
        """
        debug() works as we expect
        """
        orig_logging = green.output.logging.debug
        s = StringIO()
        green.output.logging.debug = s.write
        green.output.debug_level = 0
        debug("Nothing should happen", level=1)
        self.assertEqual('', s.getvalue())
        green.output.debug_level = 2
        debug("Something should happen", level=1)
        self.assertNotEqual('', s.getvalue())


        green.output.logging.debug = orig_logging



class TestColors(unittest.TestCase):


    def testTermcolorTrue(self):
        """
        termcolor=True results in terminal output
        """
        c = Colors(termcolor=True)
        self.assertTrue(c.termcolor)
        self.assertTrue(len(c.bold("")) > 0)


    def testTermcolorFalse(self):
        """
        termcolor=False results in no terminal output
        """
        c = Colors(termcolor=False)
        self.assertFalse(c.termcolor)
        self.assertFalse(len(c.bold("")) > 0)


    def testTermcolorAuto(self):
        """
        termcolor=None causes termcolor autodetected and set to True or False
        """
        c = Colors()
        self.assertTrue(c.termcolor in [True, False])


    def testTermstyleColorsDoNotCrash(self):
        """
        termstyle-based colors don't crash and output something
        """
        c = Colors(termcolor=True)
        for func in [c.bold, c.blue, c.green, c.red, c.yellow, c.passing,
                c.failing, c.error, c.skipped, c.unexpectedSuccess,
                c.expectedFailure, c.moduleName]:
            self.assertTrue(len(func("")) > 0)
        # c.className is a special case
        c.className("")


class TestGreenStream(unittest.TestCase):


    def testFormatText(self):
        """
        formatText returns the input text by default
        """
        s = StringIO()
        gs = GreenStream(s)
        msg = u"Unindented line.\n  Indented.\n    Double-indented.\n\n\n"
        self.assertEqual(gs.formatText(msg), str(msg))


    def testBadStringType(self):
        """
        passing the wrong stream type to GreenStream gets auto-converted
        """
        s = StringIO()
        gs = GreenStream(s)
        msg = "some string"
        if sys.version_info[0] == 3: # pragma: no cover
            bad_str = bytes(msg, 'utf-8')
        else: # pragma: no cover
            bad_str = str(msg)
        gs.write(bad_str)
        self.assertEqual(s.getvalue(), msg)
