"""
I am the green.plugin module that contains the actual Green plugin class.
"""

import logging
import os
import sys

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
            termstyle.white(
            "Green v" + version + ", " +
            "Nose " + nose.__version__ + ", " +
            "Python " + python_version)) +
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


    def handleError(self, test, error):
        self.stream.writeln("\nERROR in" + str(test) + "\n" + str(error) + "\n")


    def startContext(self, ctx):
        """
        I am called just after we load a new module or class with tests that
        need to be run.
        """
        # Watch for when our context changes to a different class
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
        self.stream.writeln(self.__format_test(test))


    def __format_module(self, module):
        self.__check_termstyle()
        return termstyle.bold(module)


    def __format_class(self, class_name):
        self.__check_termstyle()
        return termstyle.bold("  " + class_name)


    def __format_test(self, test):
        self.__check_termstyle()
        return "    " + (test.shortDescription() or str(test).split()[0])


    def __check_termstyle(self):
        # Anything that we test can potentially mess with our termstyle
        # setting. In fact, our own self-tests DO mess with it.  This function
        # restores it.
        if self.termstyle_enabled:
            termstyle.enable()
        else:
            termstyle.disable()
