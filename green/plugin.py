"""
I am the green.plugin module that contains the actual Green plugin class.
"""

import logging
import os
import sys
import traceback

from nose2 import events, util
import termstyle

from green.version import version

log = logging.getLogger('nose2.plugins.green')

__unittest = True



class Green(events.Plugin):
    """
    The test output you deserve.
    """
    alwaysOn = False
    configSection    = 'green'
    commandLineSwitch = ('G', 'green', 'The test output you deserve.')


    def __init__(self):
        self.termstyle_enabled = self.config.as_bool('color', True)
        self.module_style      = lambda x: x
        self.class_style       = lambda x: x
        self.class_indent      = 3
        self.test_indent       = 6
        self.stream            = util._WritelnDecorator(sys.stderr)
        self.num_passed        = 0
        self.last_module       = ""
        self.last_class        = ""
        self.error_list        = []
        self.category_attributes = {
            'passed'              : (self._green,  'P'),
            'failed'              : (self._red,    'F'),
            'failures'            : (self._red,    'F'),
            'error'               : (self._red,    'E'),
            'errors'              : (self._red,    'E'),
            'skipped'             : (self._blue,   'S'),
            'unexpectedSuccesses' : (self._yellow, 'U'),
            'expectedFailures'    : (self._yellow, 'X'),
        }

    def startTestRun(self, event):
        # Go ahead and start our output
        python_version = ".".join([str(x) for x in sys.version_info[0:3]])
        if self.session.verbosity > 2:
            self.stream.writeln(
                termstyle.bold(
                "Green " + version + ", " +
                "Nose2, " +
                "Python " + python_version) +
                "\n")


    def reportStartTest(self, event):
        """Handle startTest hook"""
        # Output module if it changed
        current_module = event.testEvent.test.__module__
        if current_module != self.last_module:
            event.stream.writeln(self.module_style(current_module))
            self.last_module = current_module
        # Output class if it changed
        current_class = event.testEvent.test.__class__.__name__
        if current_class != self.last_class:
            event.stream.writeln(
                    ' ' * self.class_indent + self.class_style(current_class))
            self.last_class = current_class
        # Output the current test
        test_name = (event.testEvent.test.shortDescription()
                or str(event.testEvent.test).split()[0])
        self.current_line = (' ' * self.test_indent + test_name)
        event.stream.write(self._bold(self.current_line))
        event.handled = True

        # How to get the cursor back to the start of this test output
        self.test_cursor_reposition = '\r'


    def reportSuccess(self, event):
        self._reportOutcome(event)


    def reportError(self, event):
        self._reportOutcome(event)


    def reportFailure(self, event):
        self._reportOutcome(event)


    def reportSkip(self, event):
        self._reportOutcome(event)


    def reportExpectedFailure(self, event):
        self._reportOutcome(event)


    def reportUnexpectedSuccess(self, event):
        self._reportOutcome(event)


    def reportOtherOutcome(self, event):
        # TODO - I can't figure out how to cause this to get called!
        pass


    def stopTestRun(self, event):
        self.final_time_taken = event.timeTaken


    def beforeErrorList(self, event):
        # Print out the tracebacks for failures and errors
        for testEvent in self.error_list:
            last_relevant_frames = [x for x in traceback.format_exception(*(testEvent.exc_info)) if 'unittest' not in x][-2:]
            event.stream.write(
                    '\n' + termstyle.red(testEvent.outcome.title()) +
                    ' in ' + termstyle.bold(str(testEvent.test).split()[0]) +
                    ' from ' + str(testEvent.test).split()[1].strip('()') +
                    '\n' + ''.join(last_relevant_frames))

        self._preventStreamOutput(event)


    def _preventStreamOutput(self, event):
        # For some reason, there are a few events where this is the only way to
        # stop the built-in handling from writing its own output to the stream.
        # (Well, technically it still writes it, it just doesn't make it
        # through.)  The nicer events just let you set event.handled = True
        event.stream = util._WritelnDecorator(open(os.devnull, 'w'))


    def beforeSummaryReport(self, event):
        # Alias, because we use this one a lot
        rc = event.reportCategories

        # How many, how long?
        total_tests = sum([len(x) for x in rc.values()]) + self.num_passed
        event.stream.writeln("Ran {} tests in {}".format(
            self._bold(str(total_tests)),
            self._bold(str(round(self.final_time_taken, 3))+'s')))


        # Did we pass or fail?
        if sum([len(x) for x in rc.values()]) > 0:
            verdict = self._red('FAILED')
        else:
            verdict = self._green('PASSED')

        stats_list = []
        for category in rc:
            color_func = self.category_attributes[category][0]
            if rc[category]:
                stats_list.append(
                    category + '=' +
                    color_func(str(len(rc[category]))))
        # 'passed' is a special case - nose2 doesn't include it
        color_func = self.category_attributes['passed'][0]
        stats_list.append('passed=' + color_func(str(self.num_passed)))


        stats_chunk = "(" + ", ".join(sorted(stats_list)) + ")"

        stats_line = ('\n' + verdict + ' ' + stats_chunk)

        self.stream.writeln(stats_line)

        self._preventStreamOutput(event)


    def _reportOutcome(self, event):
        """
        Handle the outcome reporting.

        """
        # Prep for the four most common outcomes
        color_func, character = self.category_attributes[event.testEvent.outcome]

        # Prep for the "Expected Failure" outcome
        if (event.testEvent.outcome == 'failed') and event.testEvent.expected:
            color_func, character = (self._yellow, 'X')

        # Pref for the "Unexpected Success" outcome
        if (event.testEvent.outcome == 'passed') and not event.testEvent.expected:
            color_func, character = (self._yellow, 'U')

        # Count 'passed' (for some reason it's not included in the normal stats)
        if (event.testEvent.outcome == 'passed') and event.testEvent.expected:
            self.num_passed += 1

        # Capture the traceback stuff for printing the error list later
        if event.testEvent.outcome in ['failed', 'error'] and not event.testEvent.expected:
            self.error_list.append(event.testEvent)

        # Overwrite the test placeholder with the test outcome
        event.stream.writeln(
                self.test_cursor_reposition +
                color_func(character) + (' ' * (self.test_indent - len(character))) +
                color_func(self.current_line.lstrip()))

        # Tell other plugins to omit output
        event.handled = True




    def _bold(self, text):
        self._restore_termstyle()
        return termstyle.bold(text)


    def _red(self, text):
        self._restore_termstyle()
        return termstyle.red(text)


    def _green(self, text):
        self._restore_termstyle()
        return termstyle.green(text)


    def _blue(self, text):
        self._restore_termstyle()
        return termstyle.blue(text)


    def _yellow(self, text):
        self._restore_termstyle()
        return termstyle.yellow(text)


    def _restore_termstyle(self):
        # Anything that we test can potentially mess with our termstyle
        # setting. In fact, our own self-tests DO mess with it.  This function
        # restores the termstyle setting.
        if self.termstyle_enabled:
            termstyle.enable()
        else:
            termstyle.disable()


    @property
    def terminal_width(self):
        rows, columns = os.popen('stty size').read().strip().split()
        return int(columns)
