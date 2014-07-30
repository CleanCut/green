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


    def testEnableHTML(self):
        """
        html=True causes HTML output
        """
        c = Colors(html=True)
        self.assertEqual(c.bold(''),  '<span style="color: rgb(255,255,255);"></span>')

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


    def testHTMLColorsDoNotCrash(self):
        """
        termstyle-based colors don't crash and output something
        """
        c = Colors(html=True)
        for func in [c.bold, c.blue, c.green, c.red, c.yellow, c.passing,
                c.failing, c.error, c.skipped, c.unexpectedSuccess,
                c.expectedFailure, c.moduleName]:
            self.assertTrue(len(func("")) > 0, "%r is not producing output" % func)
            self.assertTrue('span' in func(""))
        # c.className is a special case
        c.className("")



class TestGreenStream(unittest.TestCase):


    def testHTMLWriteNewlines(self):
        """
        html=True causes write() to transate newlines into '<br>\\n'
        """
        s = StringIO()
        gs = GreenStream(s, html=True)
        gs.write(u'\n')
        self.assertEqual(s.getvalue(), '<br>\n')


    def testFormatText(self):
        """
        formatText returns the input text by default
        """
        s = StringIO()
        gs = GreenStream(s)
        msg = u"Unindented line.\n  Indented.\n    Double-indented.\n\n\n"
        self.assertEqual(gs.formatText(msg), str(msg))


    def testHTMLFormatLine(self):
        """
        html=True causes formatLine() to add HTML '&nbsp;' instead of spaces
        """
        s = StringIO()
        gs = GreenStream(s, html=True)
        msg = u"  Indented"
        self.assertTrue('&nbsp;' in gs.formatLine(msg, indent=1))


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
