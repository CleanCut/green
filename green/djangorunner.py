"""
To try running Django tests using green you can run:

    ./manage.py test --testrunner=green.djangorunner.DjangoRunner

To make the change permanent for your project, in settings.py add:

    TEST_RUNNER="green.djangorunner.DjangoRunner"
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
import pathlib
import os
import sys
from typing import Any, Final, Sequence

from green.config import mergeConfig
from green.loader import GreenTestLoader
from green.output import GreenStream
from green.runner import run
from green.suite import GreenTestSuite

# If we're not being run from an actual django project, set up django config
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "green.djangorunner")
BASE_DIR = pathlib.Path(__file__).absolute().parent.parent
SECRET_KEY: Final[str] = ")9^_e(=cisybdt4m4+fs+_wb%d$!9mpcoy0um^alvx%gexj#jv"
DEBUG: bool = True
TEMPLATE_DEBUG: bool = True
ALLOWED_HOSTS: Sequence[str] = []
INSTALLED_APPS: Final[Sequence[str]] = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "myapp",
)
MIDDLEWARE_CLASSES: Final[Sequence[str]] = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.SessionAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)
ROOT_URLCONF: Final[str] = "myproj.urls"
WSGI_APPLICATION: Final[str] = "myproj.wsgi.application"
DATABASES: Final[dict[str, dict[str, str]]] = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "db.sqlite3"),
    }
}
LANGUAGE_CODE: Final[str] = "en-us"
TIME_ZONE: Final[str] = "UTC"
USE_I18N: bool = True
USE_L10N: bool = True
USE_TZ: bool = True
STATIC_URL: Final[str] = "/static/"
# End of django fake config stuff


def django_missing() -> None:
    raise ImportError("No django module installed")


try:
    import django

    if django.VERSION[:2] < (1, 6):  # pragma: no cover
        raise ImportError("Green integration supports Django 1.6+")
    from django.test.runner import DiscoverRunner

    class DjangoRunner(DiscoverRunner):
        def __init__(self, verbose: int = -1, **kwargs: Any):
            super().__init__(**kwargs)
            self.verbose = verbose
            self.loader = GreenTestLoader()

        @classmethod
        def add_arguments(cls, parser: ArgumentParser) -> None:
            parser.add_argument(
                "--green-verbosity",
                action="store",
                dest="verbose",
                default=-1,
                type=int,
                help="""
                    Green 'verbose' level for tests.  Value should be an integer
                    that green supports.  For example: --green-verbosity 3""",
            )
            super().add_arguments(parser)

        # FIXME: extra_tests is not used, we should either use it or update the
        #  documentation accordingly.
        def run_tests(
            self,
            test_labels: list[str] | tuple[str, ...],
            extra_tests: Any = None,
            **kwargs: Any,
        ):
            """
            Run the unit tests for all the test labels in the provided list.

            Test labels should be dotted Python paths to test modules, test
            classes, or test methods.

            A list of 'extra' tests may also be provided; these tests
            will be added to the test suite.

            Returns the number of tests that failed.
            """
            # Django setup
            self.setup_test_environment()
            django_db = self.setup_databases()

            # Green
            if isinstance(test_labels, tuple):
                test_labels = list(test_labels)
            else:
                raise ValueError("test_labels should be a tuple of strings")
            if not test_labels:
                test_labels = ["."]

            args = mergeConfig(Namespace())
            if self.verbose != -1:
                args.verbose = self.verbose
            args.targets = test_labels
            stream = GreenStream(sys.stdout)
            suite = self.loader.loadTargets(args.targets)
            if not suite:
                suite = GreenTestSuite()
            result = run(suite, stream, args)

            # Django teardown
            self.teardown_databases(django_db)
            self.teardown_test_environment()
            return self.suite_result(suite, result)

except ImportError:  # pragma: no cover
    DjangoRunner = django_missing  # type: ignore
