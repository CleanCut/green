"""
I am the green.plugin module that contains the actual Green plugin class.
"""

import logging
import os

from nose.plugins import Plugin
import termstyle

log = logging.getLogger('nose.plugins.green')



class Green(Plugin):
    """
    I am the actual 'Green' nose plugin that does all the awesome output
    formatting.
    """


    def __init__(self):
        """
        I call Plugin's __init__() and set some internal variables.
        """
        super(Green, self).__init__()
        self.name    = 'green'
        self.enabled = False
        self.score   = 199


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
        return open(os.devnull, 'w')


    def options(self, parser, env=os.environ):
        """
        I tell nosetests what options to add to its own "--help" command.
        """
        super(Green, self).options(parser, env)
        self.enabled = bool(env.get('NOSE_WITH_GREEN', False))


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

