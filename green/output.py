from __future__ import unicode_literals
from colorama.ansi import Cursor
from colorama.initialise import wrap_stream
import logging
import os
import platform
import sys
import termstyle

global debug_level
debug_level = 0

if sys.version_info[0] == 3: # pragma: no cover
    text_type = str
    unicode = None # so pyflakes stops complaining
else: # pragma: no cover
    text_type = unicode


def debug(message, level=1):
    """
    So we can tune how much debug output we get when we turn it on.
    """
    if level <= debug_level:
        logging.debug(' ' * (level - 1) * 2 + message)



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
        if termcolor == None:
            termstyle.auto()
            self.termcolor = bool(termstyle.bold(""))
        else:
            self.termcolor = termcolor
        self._restoreColor()


    def _restoreColor(self):
        """
        Unfortunately other programs (that we test) can mess with termstyle's
        global settings, so we need to reset termstyle to the correct mode after
        each test (which I think is faster than just checking whether it matches
        the current mode...)
        """
        if self.termcolor:
            termstyle.enable()
        else:
            termstyle.disable()

    # Movement
    def start_of_line(self):
        return '\r'


    def up(self, lines=1):
        return Cursor.UP(lines)


    # Real colors and styles
    def bold(self, text):
        self._restoreColor()
        return termstyle.bold(text)


    def blue(self, text):
        self._restoreColor()
        if platform.system() == 'Windows': # pragma: no cover
            # Default blue in windows is unreadable (such awful defaults...)
            return termstyle.cyan(text)
        else:
            return termstyle.blue(text)


    def green(self, text):
        self._restoreColor()
        return termstyle.green(text)


    def red(self, text):
        self._restoreColor()
        return termstyle.red(text)


    def yellow(self, text):
        self._restoreColor()
        return termstyle.yellow(text)


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
    2) Handy formatLine() and formatText() methods, which support indent levels,
       and outcome codes.
    """

    indent_spaces = 2

    def __init__(self, stream, override_appveyor=False, disable_windows=False):
        self.stream = stream
        # Ironically, AppVeyor doesn't support windows win32 system calls for
        # colors, but it WILL interpret posix ansi escape codes!
        on_windows = platform.system() == 'Windows'
        on_appveyor = os.environ.get('APPVEYOR', False)

        if (override_appveyor
                or ((on_windows and not on_appveyor)
                    and not disable_windows)): # pragma: no cover
            self.stream = wrap_stream(self.stream, None, None, None, True)
        self.closed = False


    def flush(self):
        self.stream.flush()


    def writeln(self, text=''):
        self.write(text + '\n')


    def write(self, text):
        if type(text) == bytes:
            text = text.decode('utf-8')
        self.stream.write(text)


    def formatText(self, text, indent=0, outcome_char=''):
        # We'll go through each line in the text, modify it, and store it in a
        # new list
        updated_lines = []
        for line in text.split('\n'):
            # We only need to format the line if there's something visible on it.
            if line.strip(' '):
                updated_lines.append(self.formatLine(line, indent, outcome_char))
            else:
                updated_lines.append('')
            outcome_char = '' # only the first line gets an outcome character
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
