from distutils.core import setup
import sys

from green import version

# Install a script as "green", and as "green[23]", and as
# "green-3.4" (or whatever).
scripts = [
    'green = green:main',
    'green%d = green:main' % sys.version_info[:1],
    'green-%d.%d = green:main' % sys.version_info[:2],
]


setup(
    name = 'green',
    packages = ['green'],
    version = version,
    install_requires = [
        'nose',
        'python-termstyle'
        ],
    entry_points = {
        'nose.plugins.0.10' : [
            'green = green:Green',
        ],
        'console_scripts' : scripts,
    },
    description = 'A thin-wrapper for the "nose" project that provides the colored, aligned, clean output that nose ought to have by default.  To use green, just run green (or green2 or green3, or green-X.X where X.X is your python version).  Alternatively, you can run "nosetests --with-green"',
    long_description = open('README.md').read(),
    author = 'Nathan Stocks',
    author_email = 'nathan.stocks@gmail.com',
    license = 'MIT',
    url = 'https://github.com/CleanCut/green',
    download_url = 'https://github.com/CleanCut/green/tarball/' + version,
    keywords = ['nose', 'nosetest', 'nosetests', 'plugin', 'green', 'test', 'tests', 'trial', 'functional test', 'system test', 'unit test', 'unittest', 'color', 'tabular', 'clean', 'red', 'rednose'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities'],
)
