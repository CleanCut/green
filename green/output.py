from __future__ import unicode_literals
from colorama import init, deinit, Fore, Style
from colorama.ansi import Cursor
from colorama.initialise import wrap_stream
import logging
import os
import platform
import re
import sys
from unidecode import unidecode

global debug_level
debug_level = 0

if sys.version_info[0] == 3:  # pragma: no cover
    text_type = str
    unicode = None  # so pyflakes stops complaining
else:  # pragma: no cover
    text_type = unicode


def debug(message, level=1):
    """
    So we can tune how much debug output we get when we turn it on.
    """
    if level <= debug_level:
        logging.debug(' ' * (level - 1) * 2 + str(message))


class Colors:
    """
    A class to centralize wrapping strings in terminal colors.
    """

    def __init__(self, termcolor=None):
        """
        termcolor - If None, attempt to autodetect whether we are in a terminal
            and turn on terminal colors if we think we are.  If True, force
            terminal colors on.  If False, force terminal colors off.
        """
        if termcolor is None:
            self.termcolor = sys.stdout.isatty()
        else:
            self.termcolor = termcolor

    def wrap(self, text, style):
        if self.termcolor:
            return "%s%s%s" % (style, text, Style.RESET_ALL)
        else:
            return text

    # Movement
    def start_of_line(self):
        return '\r'

    def up(self, lines=1):
        return Cursor.UP(lines)

    # Real colors and styles
    def bold(self, text):
        return self.wrap(text, Style.BRIGHT)

    def blue(self, text):
        if platform.system() == 'Windows':  # pragma: no cover
            # Default blue in windows is unreadable (such awful defaults...)
            return self.wrap(text, Fore.CYAN)
        else:
            return self.wrap(text, Fore.BLUE)

    def green(self, text):
        return self.wrap(text, Fore.GREEN)

    def red(self, text):
        return self.wrap(text, Fore.RED)

    def yellow(self, text):
        return self.wrap(text, Fore.YELLOW)

    # Abstracted colors and styles
    def passing(self, text):
        return self.green(text)

    def failing(self, text):
        return self.red(text)

    def error(self, text):
        return self.red(text)

    def skipped(self, text):
        return self.blue(text)

    def unexpectedSuccess(self, text):
        return self.yellow(text)

    def expectedFailure(self, text):
        return self.yellow(text)

    def moduleName(self, text):
        return self.bold(text)

    def className(self, text):
        return text


class GreenStream(object):
    """
    Wraps a stream-like object with the following additonal features:

    1) A handy writeln() method (which calls write() under-the-hood)
    2) Handy formatLine() and formatText() methods, which support indent
       levels, and outcome codes.
    3) Compatibility with real file objects (by implementing real file object
       methods as we discover people need them).  So far we have implemented the
       following functions just for compatibility:
           writelines(lines)
    """

    indent_spaces = 2
    _ascii_only_output = False  # default to printing output in unicode
    coverage_pattern = re.compile(r'TOTAL\s+\d+\s+\d+\s+(?P<percent>\d+)%')

    def __init__(self, stream, override_appveyor=False, disable_windows=False,
            disable_unidecode=False):
        self.disable_unidecode = disable_unidecode
        self.stream = stream
        # Ironically, AppVeyor doesn't support windows win32 system calls for
        # colors, but it WILL interpret posix ansi escape codes!
        on_windows = platform.system() == 'Windows'
        on_appveyor = os.environ.get('APPVEYOR', False)

        if (override_appveyor
                or ((on_windows and not on_appveyor)
                    and not disable_windows)):  # pragma: no cover
            self.stream = wrap_stream(self.stream, None, None, None, True)
            # set output is ascii-only
            self._ascii_only_output = True
        self.closed = False
        # z3 likes to look at sys.stdout.encoding
        try:
            self.encoding = stream.encoding
        except:
            self.encoding = 'UTF-8'
        # Susceptible to false-positives if other matching lines are output,
        # so set this to None immediately before running a coverage report to
        # guarantee accuracy.
        self.coverage_percent = None

    def flush(self):
        self.stream.flush()

    def writeln(self, text=''):
        self.write(text + '\n')

    def write(self, text):
        if type(text) == bytes:
            text = text.decode('utf-8')
        # Compensate for windows' anti-social unicode behavior
        if self._ascii_only_output and not self.disable_unidecode:
            # Windows doesn't actually want unicode, so we get
            # the closest ASCII equivalent
            text = text_type(unidecode(text))
        # Since coverage doesn't like us switching out it's stream to run extra
        # reports to look for percent covered. We should replace this with
        # grabbing the percentage directly from coverage if we can figure out
        # how.
        match = self.coverage_pattern.search(text)
        if match:
            percent_str = match.groupdict().get('percent')
            if percent_str:
                self.coverage_percent = int(percent_str)
        self.stream.write(text)

    def writelines(self, lines):
        """
        Just for better compatibility with real file objects
        """
        for line in lines:
            self.write(line)

    def formatText(self, text, indent=0, outcome_char=''):
        # We'll go through each line in the text, modify it, and store it in a
        # new list
        updated_lines = []
        for line in text.split('\n'):
            # We only need to format the line if there's something visible on
            # it.
            if line.strip(' '):
                updated_lines.append(self.formatLine(line, indent, outcome_char))
            else:
                updated_lines.append('')
            outcome_char = ''  # only the first line gets an outcome character
        # Join the list back together
        output = '\n'.join(updated_lines)
        return output

    def formatLine(self, line, indent=0, outcome_char=''):
        """
        Takes a single line, optionally adds an indent and/or outcome
        character to the beginning of the line.
        """
        actual_spaces = (indent * self.indent_spaces) - len(outcome_char)
        return (outcome_char + ' ' * actual_spaces + line)

    def isatty(self):
        """
        Wrap internal self.stream.isatty.
        """
        return self.stream.isatty()
