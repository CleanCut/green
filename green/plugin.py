"""
I am the green.plugin module that contains the actual Green plugin class.
"""

import logging
import os
import sys
import traceback

import nose
import termstyle

from green.version import version

log = logging.getLogger('nose.plugins.green')



class DevNull:
    """
    I am a dummy stream that ignores write calls.
    """
    def flush(self):
        pass
    def write(self, *arg):
        pass
    def writeln(self, *arg):
        pass



class Green(nose.plugins.Plugin):
    """
    I am the actual 'Green' nose plugin that does all the awesome output
    formatting.
    """
    name    = 'green'
    score   = 199


    def __init__(self):
        super(Green, self).__init__()
        self.unit_testing = False
        self.current_module = ''
        self.termstyle_enabled = False
        self.module_style = lambda x: x
        self.class_indent = 3
        self.class_style = lambda x: x
        self.test_indent = 6
        self.stats = {
            'PASS'  : 0,
            'FAIL'  : 0,
            'ERROR' : 0,
            'SKIP'  : 0,
        }
        self.errors = []




    def help(self):
        """
        I provide the help string for the --with-green option for nosetests.
        """
        return ("Provide colored, aligned, clean output.  The kind of output "
            "that nose ought to have by default.")


    def setOutputStream(self, stream):
        """
        I stop nosetests from outputting its own output.
        """
        self.__check_termstyle()
        # Save the real stream object to use for our output
        self.stream = stream
        # Go ahead and start our output
        python_version = ".".join([str(x) for x in sys.version_info[0:3]])
        self.stream.writeln(
            termstyle.bold(
            "Green " + version + ", " +
            "Nose " + nose.__version__ + ", " +
            "Python " + python_version) +
            "\n")
        # Discard Nose's lousy default output
        return DevNull()


    def options(self, parser, env=os.environ):
        """
        I tell nosetests what options to add to its own "--help" command.
        """
        # The superclass sets self.enabled to True if it sees the --with-green
        # flag or the NOSE_WITH_GREEN environment variable set to non-blank.
        super(Green, self).options(parser, env)


    def configure(self, options, conf):
        """
        I prep the environment once nosetests passes me which options were
        selected.  This can't be done in init, because I can't start changing
        things if I wasn't actually selected to be used.
        """
        self.__check_termstyle()
        # The superclass handles the enabling part for us
        super(Green, self).configure(options, conf)
        # Now, if we're enabled then we can get stuff ready.
        if self.enabled:
            termstyle.auto() # Works because nose hasn't touched sys.stdout yet
            self.termstyle_enabled = bool(termstyle.bold(""))

    @property
    def terminal_width(self):
        rows, columns = os.popen('stty size').read().strip().split()
        return int(columns)


    def addError(self, test, error):
        # TODO Check for SKIP condition.
        #traceback.print_exception(*error, file=self.stream)
        self.__storeError(test, error, 'ERROR')
        self.__outputResult("ERROR")


    def addFailure(self, test, error):
        self.__storeError(test, error, 'FAIL')
        self.__outputResult("FAIL")


    def addSuccess(self, test):
        self.__outputResult("PASS")


    def __storeError(self, test, error, error_type):
        self.errors.append((test, error, error_type))


    def __outputResult(self, result):
        """
        result should be 'PASS', 'FAIL', 'ERROR', or 'SKIP'
        """
        self.__check_termstyle()

        # Current color
        color_func = {
            'PASS'  : termstyle.green,
            'FAIL'  : termstyle.red,
            'ERROR' : termstyle.red,
            'SKIP'  : termstyle.blue,
        }[result]

        # How to get the cursor back to the start of this test output
        cursor_reposition = '\r'

        # Color the output
        print_result = result[0]
        self.stream.writeln(
                cursor_reposition +
                color_func(print_result) + (' ' * (self.test_indent - len(print_result))) +
                color_func(self.current_line))

        # Statistics
        self.stats[result] += 1


    def report(self, stream):
        # Print out the errors
        for i, (test, error, error_type) in enumerate(self.errors, start=1):
            last_relevant_frames = [x for x in traceback.format_exception(*error) if 'unittest' not in x][-2:]
            self.stream.write(
                    "\n" + termstyle.red(error_type) +
                    ' in ' + termstyle.bold(str(test).split()[0]) +
                    ' from ' + str(test).split()[1].strip('()') + '\n' + 
                    "".join(last_relevant_frames))


        # Did we pass or fail?
        if (self.stats['FAIL'] + self.stats['ERROR']) > 0:
            verdict = termstyle.red('FAILED')
        else:
            verdict = termstyle.green('PASSED')

        stats_list = []
        if self.stats['PASS']:
            stats_list.append('pass=' + termstyle.green(str(self.stats['PASS'])))
        if self.stats['FAIL']:
            stats_list.append('fail=' + termstyle.red(str(self.stats['FAIL'])))
        if self.stats['ERROR']:
            stats_list.append('error=' + termstyle.red(str(self.stats['ERROR'])))
        if self.stats['SKIP']:
            stats_list.append('skips=' + termstyle.blue(str(self.stats['PASS'])))

        if len(stats_list) > 1:
            total_tests = sum(self.stats.values())
            stats_list.append('total=' + termstyle.bold(str(total_tests)))

        stats_chunk = "(" + ", ".join(sorted(stats_list)) + ")"

        stats_line = ('\n' + verdict + ' ' + stats_chunk)

        self.stream.writeln(stats_line)


    def startContext(self, ctx):
        """
        I am called just after we load a new module or class with tests that
        need to be run.
        """
        # Watch for when our context changes to a different class
        self.current_line = ""
        if type(ctx) == type:
            # If this class is in a different module, output the new module first
            if ctx.__module__ != self.current_module:
                self.stream.writeln(self.__format_module(ctx.__module__))
                self.current_module = ctx.__module__
            # Now output the class itself
            self.stream.writeln(self.__format_class(ctx.__name__))


    def startTest(self, test):
        """
        I am called before each test is run.
        """
        if not self.unit_testing:
            self.unit_testing = True
        self.stream.write(self.__format_test(test))
        self.stream.flush()


    def __format_module(self, module):
        self.__check_termstyle()
        return self.module_style(module)


    def __format_class(self, class_name):
        self.__check_termstyle()
        return self.class_style(' ' * self.class_indent + class_name)


    def __format_test(self, test):
        self.__check_termstyle()
        test_name = (test.shortDescription() or str(test).split()[0])
        self.current_line = test_name
        return (' ' * self.test_indent + self.current_line)


    def __check_termstyle(self):
        # Anything that we test can potentially mess with our termstyle
        # setting. In fact, our own self-tests DO mess with it.  This function
        # restores it.
        if self.termstyle_enabled:
            termstyle.enable()
        else:
            termstyle.disable()
