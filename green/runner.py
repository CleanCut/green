import logging
import sys
import termstyle
import time
import traceback
from unittest.result import TestResult
from unittest.signals import registerResult
import warnings

from green.version import __version__

global debug_level
debug_level = 0


def debug(message, level=0):
    """So we can tune how much debug output we get when we turn it on."""
    if level <= debug_level:
        logging.debug(message)



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


    def red(self, text):
        self._restoreColor()
        if self.html:
            return '<span style="color: rgb(237,73,62)">{}</span>'.format(text)
        else:
            return termstyle.red(text)


    def green(self, text):
        self._restoreColor()
        if self.html:
            return '<span style="color: rgb(0,194,0)">{}</span>'.format(text)
        else:
            return termstyle.green(text)


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




class GreenTestResult(TestResult):
    """A test result class that prints clean Green test results to a stream.

    Used by GreenTestRunner.
    """

    def __init__(self, stream, descriptions, verbosity, colors=None,
            html=False):
        """stream, descriptions, and verbosity are as in
        unittest.runner.TextTestRunner.

        colors - An instance of Colors.
        """
        super(GreenTestResult, self).__init__(stream, descriptions, verbosity)
        self.stream = stream
        self.showAll = verbosity > 1
        self.dots = verbosity == 1
        self.verbosity = verbosity
        self.descriptions = descriptions
        self.colors = colors or Colors()
        self.last_module = ''
        self.last_class = ''
        self.all_errors = []
        self.passing = []


    def getDescription(self, test):
        doc_first_line = test.shortDescription()
        if self.descriptions and doc_first_line:
            return '\n'.join((str(test), doc_first_line))
        else:
            return str(test)


    def startTest(self, test):
        super(GreenTestResult, self).startTest(test)
        # Get our bearings
        current_module = test.__module__
        current_class  = test.__class__.__name__

        # Output
        if self.showAll:
            # Module...if it changed.
            if current_module != self.last_module:
                self.stream.writeln(self.colors.moduleName(current_module))
            # Class...if it changed.
            if current_class != self.last_class:
                self.stream.writeln(self.colors.className(
                    self.stream.formatText(current_class, indent=1)))
            # Test name or description
            self.test_output_line = self._testDescription(test)
            if not self.colors.html:
                # In the terminal, we will write a placeholder, and then
                # rewrite it in color after the test has run.
                self.stream.write(
                    self.colors.bold(
                        self.stream.formatLine(self.test_output_line, indent=2)))
            self.stream.flush()

        # Set state for next time
        if current_module != self.last_module:
            self.last_module = current_module
        if current_class != self.last_class:
            self.last_class = current_class


    def _testDescription(self, test):
        return test.shortDescription() or str(test).split()[0]


    def _reportOutcome(self, test, outcome_char, color_func, err=None, reason=''):
        if self.showAll:
            # Move the cursor back to the start of the line in terminal mode
            if not self.colors.html:
                self.stream.write('\r')
            self.stream.write(
                color_func(
                    self.stream.formatLine(
                        self.test_output_line,
                        indent=2,
                        outcome_char=outcome_char)
                )
            )
            if reason:
                self.stream.write(color_func(' -- ' + reason))
            self.stream.writeln()
            self.stream.flush()
        elif self.dots:
            self.stream.write(color_func(outcome_char))
            self.stream.flush()


    def addSuccess(self, test):
        super(GreenTestResult, self).addSuccess(test)
        self.passing.append(test)
        self._reportOutcome(test, '.', self.colors.passing)


    def addError(self, test, err):
        super(GreenTestResult, self).addError(test, err)
        self.all_errors.append((test, self.colors.error, 'Error', err))
        self._reportOutcome(test, 'E', self.colors.error, err)


    def addFailure(self, test, err):
        super(GreenTestResult, self).addFailure(test, err)
        self.all_errors.append((test, self.colors.error, 'Failure', err))
        self._reportOutcome(test, 'F', self.colors.failing, err)


    def addSkip(self, test, reason):
        super(GreenTestResult, self).addSkip(test, reason)
        self._reportOutcome(
                test, 's', self.colors.skipped, err=None, reason=reason)


    def addExpectedFailure(self, test, err):
        super(GreenTestResult, self).addExpectedFailure(test, err)
        self._reportOutcome(test, 'x', self.colors.expectedFailure, err)


    def addUnexpectedSuccess(self, test):
        super(GreenTestResult, self).addUnexpectedSuccess(test)
        self._reportOutcome(test, 'u', self.colors.expectedFailure)


    def printErrors(self):
        if not self.all_errors:
            return
        if self.dots:
            self.stream.writeln()
        for (test, color_func, outcome, err) in self.all_errors:
            # Header Line
            self.stream.writeln(
                    '\n' + color_func(outcome) +
                    ' in ' + self.colors.bold(str(test).split()[0]) +
                    ' from ' + str(test).split()[1].strip('()'))

            # Frame Line
            relevant_frames = []
            for i, frame in enumerate(traceback.format_exception(*err)):
                debug('\n' + '*' * 30 + "Frame {}:".format(i) + '*' * 30
                        + "\n{}".format(self.colors.yellow(frame)), level = 3)
                # Ignore useless frames
                if self.verbosity < 4:
                    if frame.strip() == "Traceback (most recent call last):":
                        continue
                reindented_lines = []
                # If we're in html, space-based indenting needs to be converted.
                if self.colors.html:
                    for line in frame.split('\n'):
                        frame_indent = 0
                        while line[:2] == '  ':
                            line = line[2:]
                            frame_indent += 1
                        line = self.stream.formatLine(line, indent=frame_indent)
                        reindented_lines.append(line)
                    frame = "\n".join(reindented_lines)
                # Done with this frame, capture it.
                relevant_frames.append(frame)
            self.stream.write(''.join(relevant_frames))



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
        self.html = html


    def __getattr__(self, attr):
        if attr in ('stream', '__getstate__'):
            raise AttributeError(attr)
        return getattr(self.stream,attr)


    def writeln(self, text=''):
        self.write(text + '\n')


    def write(self, text):
        if self.html:
            text = text.replace('\n', '<br>\n')
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
        indent_pixels = actual_spaces * self.pixels_per_space
        if self.html:
            return (outcome_char +
                    self.margin_template.format(indent_pixels, line))
        else:
            return outcome_char + ' ' * actual_spaces + line





class GreenTestRunner(object):
    """A test runner class that displays results in Green's clean style.
    """


    def __init__(self, stream=None, descriptions=True, verbosity=1,
                 failfast=False, buffer=False, warnings=None,
                 colors=None, html=None):
        """All arguments ar as in unittest.TextTestRunner except...

        stream - Any stream passed in will be wrapped in a GreenStream
        colors - A Colors object.  Default colors will be used if not provided.
        Used to determine whether html mode is desired as well.
        """
        if stream is None:
            stream = sys.stderr
        if not issubclass(GreenStream, type(stream)):
            stream = GreenStream(stream)
        self.stream = stream
        self.descriptions = descriptions
        self.verbosity = verbosity
        self.failfast = failfast
        self.buffer = buffer
        self.warnings = warnings
        self.colors = colors or Colors()


    def _makeResult(self):
        return GreenTestResult(
                self.stream, self.descriptions, self.verbosity, self.colors)


    def run(self, test):
        "Run the given test case or test suite."
        # Really verbose information
        if self.colors.html:
            self.stream.write(
                    '<div style="font-family: Monaco, \'Courier New\', monospace; color: rgb(170,170,170); background: rgb(0,0,0); padding: 14px;">')
        python_version = ".".join([str(x) for x in sys.version_info[0:3]])
        if self.verbosity > 2:
            self.stream.writeln(
                self.colors.bold(
                "Green " + __version__ + ", " +
                "Python " + python_version) +
                "\n")
        result = self._makeResult()
        registerResult(result)
        result.failfast = self.failfast
        result.buffer = self.buffer
        with warnings.catch_warnings():
            if self.warnings:
                # if self.warnings is set, use it to filter all the warnings
                warnings.simplefilter(self.warnings)
                # if the filter is 'default' or 'always', special-case the
                # warnings from the deprecated unittest methods to show them
                # no more than once per module, because they can be fairly
                # noisy.  The -Wd and -Wa flags can be used to bypass this
                # only when self.warnings is None.
                if self.warnings in ['default', 'always']:
                    warnings.filterwarnings('module',
                            category=DeprecationWarning,
                            message='Please use assert\w+ instead.')
            startTime = time.time()
            startTestRun = getattr(result, 'startTestRun', None)
            if startTestRun is not None:
                startTestRun()
            try:
                test(result)
            finally:
                stopTestRun = getattr(result, 'stopTestRun', None)
                if stopTestRun is not None:
                    stopTestRun()
            stopTime = time.time()
        timeTaken = stopTime - startTime
        result.printErrors()
        run = result.testsRun
        if run:
            self.stream.writeln()
        self.stream.writeln("Ran %s test%s in %ss" %
            (self.colors.bold(str(run)),
            run != 1 and "s" or "",
            self.colors.bold("%.3f" % timeTaken)))
        self.stream.writeln()

        results = [
            (result.errors, 'errors', self.colors.error),
            (result.expectedFailures, 'expected_failures',
                self.colors.expectedFailure),
            (result.failures, 'failures', self.colors.failing),
            (result.passing, 'passes', self.colors.passing),
            (result.skipped, 'skips', self.colors.skipped),
            (result.unexpectedSuccesses, 'unexpected_successes',
                self.colors.unexpectedSuccess),
        ]
        stats = []
        for obj_list, name, color_func in results:
            if obj_list:
                stats.append("{}={}".format(name, color_func(str(len(obj_list)))))
        if not stats:
            self.stream.writeln(self.colors.passing("No Tests Found"))
        else:
            grade = self.colors.passing('OK')
            if result.errors or result.failures:
                grade = self.colors.failing('FAILED')
            self.stream.writeln("{} ({})".format(grade, ', '.join(stats)))
        if self.colors.html:
            self.stream.writeln('</div>')
        return result
