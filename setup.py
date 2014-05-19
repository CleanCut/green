from setuptools import setup, find_packages
import os
import sys

version = open(os.path.join(os.path.dirname(__file__), 'green', 'VERSION')).read().strip()

long_description = '\n'.join(list(filter(lambda x: not x.startswith('[!'),
                             open('README.md').read().split('\n'))))

dependencies = [
    'python-termstyle'
]
if sys.version_info[0] == 2:
    dependencies.append('mock')

setup(
    name = 'green',
    packages = find_packages(),
    package_data = {'green' : ['VERSION']},
    version = version,
    install_requires = dependencies,
    entry_points = {
        'console_scripts' : [
            'green = green:main',
            'green%d = green:main' % sys.version_info[:1],    # green2 or green3
            'green%d.%d = green:main' % sys.version_info[:2], # green3.4 etc.
            ],
    },
    test_suite='green.test',
    description = 'Green is a clean, colorful test runner for Python unit tests.  Compare it to nose or trial.',
    long_description = long_description,
    author = 'Nathan Stocks',
    author_email = 'nathan.stocks@gmail.com',
    license = 'MIT',
    url = 'https://github.com/CleanCut/green',
    download_url = 'https://github.com/CleanCut/green/tarball/' + version,
    keywords = ['nose', 'nose2', 'trial', 'tox', 'green', 'test', 'tests', 'functional test', 'system test', 'unit test', 'unittest', 'color', 'tabular', 'clean', 'red', 'rednose'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities'],
)
