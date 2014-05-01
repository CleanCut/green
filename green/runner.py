import sys
import termstyle
import time
from unittest.result import TestResult
from unittest.signals import registerResult
import warnings

from green.version import __version__



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
            return '<strong>{}</strong>'.format(text)
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
    separator1 = '=' * 70
    separator2 = '-' * 70

    def __init__(self, stream, descriptions, verbosity, colors=None, html=False):
        """stream, descriptions, and verbosity are as in
        unittest.runner.TextTestRunner.

        colors - An instance of Colors.
        """
        super(GreenTestResult, self).__init__(stream, descriptions, verbosity)
        self.stream = stream
        self.showAll = verbosity > 1
        self.dots = verbosity == 1
        self.descriptions = descriptions
        self.colors = colors or Colors()
        self.last_module = ''
        self.last_class = ''


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
            self.test_output_line = test.shortDescription() or str(test).split()[0]
            if not self.colors.html:
                # In the terminal, we will write a placeholder, and then
                # rewrite it in color after the test has run.
                self.stream.write(self.stream.formatLine(self.test_output_line, indent=2))
            self.stream.flush()

        # Set state for next time
        if current_module != self.last_module:
            self.last_module = current_module
        if current_class != self.last_class:
            self.last_class = current_class


    def addSuccess(self, test):
        super(GreenTestResult, self).addSuccess(test)
        self._reportOutcome(test, 'P', self.colors.passing)


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


    def addError(self, test, err):
        super(GreenTestResult, self).addError(test, err)
        self._reportOutcome(test, 'E', self.colors.error, err)


    def addFailure(self, test, err):
        super(GreenTestResult, self).addFailure(test, err)
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
        if self.dots or self.showAll:
            self.stream.writeln()
        self.printErrorList('ERROR', self.errors)
        self.printErrorList('FAIL', self.failures)


    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (flavour,self.getDescription(test)))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)



class GreenStream(object):
    """Wraps a stream-like object with the following additonal features:

    1) A handy writeln() method (which calls write() under-the-hood)
    2) Augment the write() method to support specified indentation levels.
    3) Augment the write() method to support HTML5 output (converting
       indentation and line breaks to HTML5)
    """

    pixels_per_space = 8
    indent_spaces = 3
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
        # Join the list back together with the appropriate line separators
        if self.html:
            output = '<br>\n'.join(updated_lines)
        else:
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
        if hasattr(result, 'separator2'):
            self.stream.writeln(result.separator2)
        run = result.testsRun
        self.stream.writeln("Ran %d test%s in %.3fs" %
                            (run, run != 1 and "s" or "", timeTaken))
        self.stream.writeln()

        expectedFails = unexpectedSuccesses = skipped = 0
        try:
            results = map(len, (result.expectedFailures,
                                result.unexpectedSuccesses,
                                result.skipped))
        except AttributeError:
            pass
        else:
            expectedFails, unexpectedSuccesses, skipped = results

        infos = []
        if not result.wasSuccessful():
            self.stream.write("FAILED")
            failed, errored = len(result.failures), len(result.errors)
            if failed:
                infos.append("failures=%d" % failed)
            if errored:
                infos.append("errors=%d" % errored)
        else:
            self.stream.write("OK")
        if skipped:
            infos.append("skipped=%d" % skipped)
        if expectedFails:
            infos.append("expected failures=%d" % expectedFails)
        if unexpectedSuccesses:
            infos.append("unexpected successes=%d" % unexpectedSuccesses)
        if infos:
            self.stream.writeln(" (%s)" % (", ".join(infos),))
        else:
            self.stream.write("\n")
        return result
