"""Registers the green command with setuptools."""

from __future__ import annotations

import functools
import sys
from typing import TYPE_CHECKING

from setuptools import Command

from green.config import parseArguments
from green.cmdline import main

if TYPE_CHECKING:
    from argparse import Action


def get_user_options() -> list[tuple[str, str | None, str | None]]:
    # When running "python setup.py --help-commands", setup.py will call this
    # function -- but green isn't actually being called.
    if "--help-commands" in sys.argv:
        return []

    args = parseArguments()
    options: list[tuple[str, str | None, str | None]] = []

    action: Action
    for action in args.store_opt.actions:
        names = [name.lstrip("-") for name in action.option_strings]
        short_name: str | None
        if len(names) == 1:
            full_name = names[0]
            short_name = None
        else:
            # TODO: We might want to pick the longer of the two for full_name.
            full_name = names[1]
            short_name = names[0]
        if not action.const:
            full_name += "="
        options.append((full_name, short_name, action.help))

    return options


class green(Command):
    command_name = "green"
    description = "Run unit tests using green"

    @functools.cached_property
    def user_options(self) -> list[tuple[str, str | None, str | None]]:
        return get_user_options()

    def initialize_options(self) -> None:
        for name, _, _ in self.user_options:
            setattr(self, name.replace("-", "_").rstrip("="), None)

    def finalize_options(self) -> None:
        pass

    def run(self) -> None:
        self.ensure_finalized()

        if self.distribution.install_requires:
            self.distribution.fetch_build_eggs(self.distribution.install_requires)
        if self.distribution.tests_require:
            self.distribution.fetch_build_eggs(self.distribution.tests_require)

        script_args = self.distribution.script_args[1:]
        if self.distribution.test_suite is not None:
            script_args.append(self.distribution.test_suite)

        error_code = main(script_args)
        if error_code:
            sys.exit(error_code)
