from __future__ import unicode_literals
from io import StringIO
import platform
import sys
import unittest


try:
    from unittest.mock import MagicMock, patch
except:
    from mock import MagicMock, patch

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
        self.assertEqual("", s.getvalue())
        green.output.debug_level = 2
        debug("Something should happen", level=1)
        self.assertNotEqual("", s.getvalue())

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

    def testUp(self):
        """
        calling up gives us a non-blank string
        """
        c = Colors()
        up = c.up()
        self.assertEqual(type(up), str)
        self.assertNotEqual(up, "")

    def testTerminalColorsDoNotCrash(self):
        """
        terminal colors don't crash, and they output something
        """
        c = Colors(termcolor=True)
        for func in [
            c.bold,
            c.blue,
            c.green,
            c.red,
            c.yellow,
            c.passing,
            c.failing,
            c.error,
            c.skipped,
            c.unexpectedSuccess,
            c.expectedFailure,
            c.moduleName,
        ]:
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
        msg = "Unindented line.\n  Indented.\n    Double-indented.\n\n\n"
        self.assertEqual(gs.formatText(msg), str(msg))

    def testBadStringType(self):
        """
        passing the wrong stream type to GreenStream gets auto-converted
        """
        s = StringIO()
        gs = GreenStream(s)
        msg = "some string"
        if sys.version_info[0] == 3:  # pragma: no cover
            bad_str = bytes(msg, "utf-8")
        else:  # pragma: no cover
            bad_str = str(msg)
        gs.write(bad_str)
        self.assertEqual(s.getvalue(), msg)

    def testDisableWindowsTrue(self):
        """
        disable_windows=True: ANSI color codes are present in the stream
        """
        c = Colors(termcolor=True)
        s = StringIO()
        gs = GreenStream(s, disable_windows=True)
        msg = c.red("some colored string")
        gs.write(msg)
        self.assertEqual(len(gs.stream.getvalue()), len(msg))

    @unittest.skipIf(
        platform.system() != "Windows",
        "Colorama won't strip ANSI unless running on Windows",
    )
    def testDisableWindowsFalse(self):
        """
        disable_windows=False: Colorama strips ANSI color codes from the stream
        """
        c = Colors(termcolor=True)
        s = StringIO()
        gs = GreenStream(s, override_appveyor=True, disable_windows=False)
        colored_msg = c.red("a")
        gs.write(colored_msg)
        import colorama

        self.assertTrue(issubclass(type(gs.stream), colorama.ansitowin32.StreamWrapper))

    @patch("green.output.unidecode")
    def testUnidecodeAppveyor(self, mock_unidecode):
        """
        When I'm on Appveyor, I run text through Unidecode
        """
        mock_unidecode.return_value = "something"
        s = StringIO()
        gs = GreenStream(s, override_appveyor=True)
        gs.write("something")
        self.assertTrue(mock_unidecode.called)

    @patch("green.output.unidecode")
    def testUnidecodeDisabled(self, mock_unidecode):
        """
        Unidecode can be disabled
        """
        mock_unidecode.return_value = "something"
        s = StringIO()
        gs = GreenStream(s, override_appveyor=True, disable_unidecode=True)
        gs.write("something")
        self.assertFalse(mock_unidecode.called)

    def testWritelines(self):
        """
        Compatibility function writelines(lines) repeatedly calls write()
        """
        s = StringIO()
        gs = GreenStream(s)
        gs.write = MagicMock()
        gs.writelines(["one", "two", "three"])
        self.assertEqual(len(gs.write.mock_calls), 3)

    def testCoverageDetection(self):
        """
        write() detects a coverage percentage flying by
        """
        s = StringIO()
        gs = GreenStream(s)
        gs.write(
            "\n---------------------------------------------------\nTOTAL                   896    367    59%\nRan"
        )
        self.assertEqual(gs.coverage_percent, 59)

    def testEncodingMirrors(self):
        """
        The encoding of a stream gets mirrored through
        """
        s = StringIO()
        encoding = "aoeu"
        try:
            encoding = s.encoding
        except:
            s.encoding = encoding
        gs = GreenStream(s)
        self.assertEqual(gs.encoding, encoding)

    def testEncodingDefault(self):
        """
        The encoding defaults to 'UTF-8' if we can't find an encoding.
        """
        s = MagicMock(spec=1)
        gs = GreenStream(s)
        self.assertEqual(gs.encoding, "UTF-8")
