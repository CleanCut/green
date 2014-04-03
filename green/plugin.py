import logging
import os

from nose.plugins import Plugin

log = logging.getLogger('nose.plugins.green')



class Green(Plugin):

    def __init__(self):
        super(Green, self).__init__()
        self.name    = 'green'
        self.enabled = False
        self.score   = 199

    def help(self):
        return "Provide colored, aligned, clean output."


    def setOutputStream(self, stream):
        # Save the real stream object to use for our output
        self.stream = stream
        # Discard Nose's lousy default output
        class DevNull:
            def write(self, *arg):
                pass
            def writeln(self, *arg):
                pass
        return DevNull()


    def options(self, parser, env=os.environ):
        green_enabled   = bool(env.get('NOSE_GREEN', False))

        parser.add_option(
                "--with-green",
                action="store_true",
                default=green_enabled,
                dest="green",
                help=("Enable the green plugin, and get the output you've been "
                     "waiting for.  You can also set NOSE_GREEN=1 in your "
                     "environment."))

#        parser.add_option(
#                "--green-immediate",
#                action="store_true",
#                default=False,
#                help="Show errors and failures as they happen, instead of at the end"
#        )
