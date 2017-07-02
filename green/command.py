from __future__ import unicode_literals
from __future__ import print_function

try:
    from setuptools import Command
except ImportError:
    from distutils.cmd import Command

from green.config import parseArguments
from green.cmdline import main


def get_user_options():
    r = parseArguments()

    options = []

    for action in r.store_opt.actions:
        names = [name.lstrip('-') for name in action.option_strings]
        if len(names) == 1: names.insert(0, None)
        if not action.const: names[1] += "="
        options.append((names[1], names[0], action.help))

    return options


class green(Command):

    command_name = "green"
    description = " green is a clean, colorful, fast python test runner"
    user_options = get_user_options()

    def initialize_options(self):
        for name, _, _ in self.user_options:
            setattr(self, name.replace('-', '_'), None)

    def finalize_options(self):
        pass

    def run(self):
        self.ensure_finalized()

        #print(vars(self.distribution))
        error_code = main(self.distribution.script_args[1:])
        if error_code:
            sys.exit(error_code)
