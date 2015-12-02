from __future__ import unicode_literals
"""
To try running Django tests using green you can run:

    ./manage.py test --testrunner=green.djangorunner.DjangoRunner

To make the change permanent for your project, in settings.py add:

    TEST_RUNNER=green.djangorunner.DjangoRunner
"""

from argparse import Namespace
import os
import sys

from green.config import mergeConfig
from green.loader import loadTargets
from green.output import GreenStream
from green.runner import run
from green.suite import GreenTestSuite

# If we're not being run from an actual django project, set up django config
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'green.djangorunner')
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SECRET_KEY = ')9^_e(=cisybdt4m4+fs+_wb%d$!9mpcoy0um^alvx%gexj#jv'
DEBUG = True
TEMPLATE_DEBUG = True
ALLOWED_HOSTS = []
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',
)
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
ROOT_URLCONF = 'myproj.urls'
WSGI_APPLICATION = 'myproj.wsgi.application'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'
# End of django fake config stuff


def django_missing():
    raise ImportError("No django module installed")


try:
    import django
    if django.VERSION[:2] < (1, 6): # pragma: no cover
        raise ImportError("Green integration supports Django 1.6+")
    from django.test.runner import DiscoverRunner



    class DjangoRunner(DiscoverRunner):


        def run_tests(self, test_labels, extra_tests=None, **kwargs):
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
            if type(test_labels) == tuple:
                test_labels = list(test_labels)
            else:
                raise ValueError("test_labels should be a tuple of strings")
            if not test_labels:
                test_labels = ['.']

            args = mergeConfig(Namespace())
            args.targets = test_labels
            stream = GreenStream(sys.stdout)
            suite = loadTargets(args.targets)
            if not suite:
                suite = GreenTestSuite()
            result = run(suite, stream, args)

            # Django teardown
            self.teardown_databases(django_db)
            self.teardown_test_environment()
            return self.suite_result(suite, result)



except ImportError: # pragma: no cover
    DjangoRunner = django_missing
