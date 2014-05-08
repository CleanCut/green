import os
import sys
import unittest

from green.output import Colors, GreenStream



class TestColors(unittest.TestCase):


    def testTermcolorTrue(self):
        "termcolor=True results in terminal output"
        c = Colors(termcolor=True)
        self.assertTrue(c.termcolor)
        self.assertTrue(len(c.bold("")) > 0)


    def testTermcolorFalse(self):
        "termcolor=False results in no terminal output"
        c = Colors(termcolor=False)
        self.assertFalse(c.termcolor)
        self.assertFalse(len(c.bold("")) > 0)


    def testTermcolorAuto(self):
        "termcolor=None causes termcolor autodetected and set to True or False"
        c = Colors()
        self.assertTrue(c.termcolor in [True, False])


    def testEnableHTML(self):
        "html=True causes HTML output"
        c = Colors(html=True)
        self.assertEqual(c.bold(''),  '<span style="color: rgb(255,255,255);"></span>')

    def testTermstyleColorsDoNotCrash(self):
        "termstyle-based colors don't crash and output something"
        c = Colors(termcolor=True)
        for func in [c.bold, c.blue, c.green, c.red, c.yellow, c.passing,
                c.failing, c.error, c.skipped, c.unexpectedSuccess,
                c.expectedFailure, c.moduleName]:
            self.assertTrue(len(func("")) > 0)
        # c.className is a special case
        c.className("")


    def testHTMLColorsDoNotCrash(self):
        "termstyle-based colors don't crash and output something"
        c = Colors(html=True)
        for func in [c.bold, c.blue, c.green, c.red, c.yellow, c.passing,
                c.failing, c.error, c.skipped, c.unexpectedSuccess,
                c.expectedFailure, c.moduleName]:
            self.assertTrue(len(func("")) > 0, "%r is not producing output" % func)
            self.assertTrue('span' in func(""))
        # c.className is a special case
        c.className("")



class TestGreenStream(unittest.TestCase):


    pass
