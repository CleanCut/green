from __future__ import unicode_literals
from __future__ import print_function

import sys

try:
    from setuptools import Command
except ImportError: # pragma: no cover
    from distutils.cmd import Command

from green.config import parseArguments
from green.cmdline import main


def get_user_options():

    # When running "python setup.py --help-commands", setup.py will call this
    # function -- but green isn't actually being called.
    if "--help-commands" in sys.argv:
        return []

    r = parseArguments()
    options = []

    for action in r.store_opt.actions:
        names = [str(name.lstrip('-')) for name in action.option_strings]
        if len(names) == 1: names.insert(0, None)
        if not action.const: names[1] += str("=")
        options.append((names[1], names[0], action.help))

    return options


class green(Command):

    command_name = "green"
    description = "Run unit tests using green"
    user_options = get_user_options()

    def initialize_options(self):
        for name, _, _ in self.user_options:
            setattr(self, name.replace('-', '_').rstrip('='), None)

    def finalize_options(self):
        pass

    def run(self):
        self.ensure_finalized()

        if self.distribution.install_requires:
            self.distribution.fetch_build_eggs(
                self.distribution.install_requires)
        if self.distribution.tests_require:
            self.distribution.fetch_build_eggs(
                self.distribution.tests_require)

        script_args = self.distribution.script_args[1:]
        if self.distribution.test_suite is not None:
            script_args.append(self.distribution.test_suite)

        error_code = main(script_args)
        if error_code:
            sys.exit(error_code)
