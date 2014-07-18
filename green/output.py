from __future__ import unicode_literals
import logging
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
    """So we can tune how much debug output we get when we turn it on."""
    if level <= debug_level:
        logging.debug(' ' * (level - 1) * 2 + message)



class Colors:
    """A class to centralize wrapping strings in colors.  Supports terminal
    colors or HTML5 colors.  (Not at the same time)
    """


    def __init__(self, termcolor=None, html=False):
        """
        termcolor - If None, attempt to autodetect whether we are in a terminal
            and turn on terminal colors if we think we are.  If True, force
            terminal colors on.  If False, force terminal colors off.  This
            value is ignored if html is True.

        html - If true, enables HTML output and causes termcolor to be ignored.
        """
        self.html = html
        if html:
            termcolor = False

        if termcolor == None:
            termstyle.auto()
            self.termcolor = bool(termstyle.bold(""))
        else:
            self.termcolor = termcolor

        self._restoreColor()


    def _restoreColor(self):
        """Unfortunately other programs (that we test) can mess with termstyle's
        global settings, so we need to reset termstyle to the correct mode after
        each test (which I think is faster than just checking whether it matches
        the current mode...)
        """
        if self.termcolor:
            termstyle.enable()
        else:
            termstyle.disable()


    # Real colors and styles
    def bold(self, text):
        self._restoreColor()
        if self.html:
            return '<span style="color: rgb(255,255,255);">{}</span>'.format(text)
        else:
            return termstyle.bold(text)


    def blue(self, text):
        self._restoreColor()
        if self.html:
            return '<span style="color: rgb(0,128,255)">{}</span>'.format(text)
        else:
            return termstyle.blue(text)


    def green(self, text):
        self._restoreColor()
        if self.html:
            return '<span style="color: rgb(0,194,0)">{}</span>'.format(text)
        else:
            return termstyle.green(text)


    def red(self, text):
        self._restoreColor()
        if self.html:
            return '<span style="color: rgb(237,73,62)">{}</span>'.format(text)
        else:
            return termstyle.red(text)


    def yellow(self, text):
        self._restoreColor()
        if self.html:
            return '<span style="color: rgb(225,140,0)">{}</span>'.format(text)
        else:
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
    """Wraps a stream-like object with the following additonal features:

    1) A handy writeln() method (which calls write() under-the-hood)
    2) Augment the write() method to support HTML5 output (converting
       indentation and line breaks to HTML5)
    3) Handy formatLine() and formatText() methods, which support HTML5, indent
       levels, and outcome codes.
    """

    pixels_per_space = 10
    indent_spaces = 2
    margin_template = '<span style="margin-left: {}px;">{}</span>'

    def __init__(self, stream, html=False):
        self.stream = stream
        if platform.system() == 'Windows': # pragma: no cover
            from colorama.initialise import wrap_stream
            self.stream = wrap_stream(self.stream, None, None, None, True)
        self.html = html


    def flush(self):
        self.stream.flush()


    def writeln(self, text=''):
        self.write(text + '\n')


    def write(self, text):
        if self.html:
            text = text.replace('\n', '<br>\n')
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
        """Takes a single line, optionally adds an indent and/or outcome
        character to the beginning of the line."""
        actual_spaces = (indent * self.indent_spaces) - len(outcome_char)
        space_char = ' '
        if self.html:
            space_char = '&nbsp;'
        return (outcome_char + space_char * actual_spaces + line)

