"""
I am the green.plugin module that contains the actual Green plugin class.
"""

import logging
import os

from nose.plugins import Plugin
import termstyle

from green.version import version

log = logging.getLogger('nose.plugins.green')



class DevNull:
    """
    I am a dummy stream that ignores write calls.
    """
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


    def help(self):
        """
        I provide the help string for...?
        """
        return ("Provide colored, aligned, clean output.  The kind of output "
            "that nose ought to have by default.")


    def setOutputStream(self, stream):
        """
        I stop nosetests from outputting its own output.
        """
        # Save the real stream object to use for our output
        self.stream = stream
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
        # The superclass handles the enabling part for us
        super(Green, self).configure(options, conf)
        # Now, if we're enabled then we can get stuff ready.
        if self.enabled:
            termstyle.auto()
            print(termstyle.green("GREEN!"))

