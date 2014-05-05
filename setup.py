from setuptools import setup
import os
import sys

version = open(os.path.join(os.path.dirname(__file__), 'green', 'VERSION')).read().strip()

long_description = '\n'.join(list(filter(lambda x: not x.startswith('[!'),
                             open('README.md').read().split('\n'))))

setup(
    name = 'green',
    packages = ['green'],
    package_data = {'green' : ['VERSION']},
    version = version,
    install_requires = [
        'python-termstyle'
        ],
    entry_points = {
        'console_scripts' : [
            'green = green:main',
            'green%d = green:main' % sys.version_info[:1],     # green2 or green3
            'green-%d.%d = green:main' % sys.version_info[:2], # green-3.4 etc.
            ],
    },
    description = 'Green is a clean, colorful test runner for Python unit tests.  Compare it to nose, nose2, and trial.',
    long_description = long_description,
    author = 'Nathan Stocks',
    author_email = 'nathan.stocks@gmail.com',
    license = 'MIT',
    url = 'https://github.com/CleanCut/green',
    download_url = 'https://github.com/CleanCut/green/tarball/' + version,
    keywords = ['nose', 'nose2', 'trial', 'green', 'test', 'tests', 'functional test', 'system test', 'unit test', 'unittest', 'color', 'tabular', 'clean', 'red', 'rednose'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities'],
)
