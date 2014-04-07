from distutils.core import setup

from green import version

setup(
    name = 'green',
    packages = ['green'],
    version = version,
    entry_points = {
        'nose.plugins.0.10' : [
            'green = green:Green',
            ]
        },
    description = '!!! This module is still Pre-Alpha !!!  A plugin for nose that provides the colored, aligned, clean output that nose ought to have by default.',
    long_description = open('README.md').read(),
    author = 'Nathan Stocks',
    author_email = 'nathan.stocks@gmail.com',
    license = 'MIT',
    url = 'https://github.com/CleanCut/green',
    download_url = 'https://github.com/CleanCut/green/tarball/' + version,
    keywords = ['nose', 'nosetest', 'nosetests', 'plugin', 'green', 'test', 'unittest', 'color', 'tabular', 'clean', 'red', 'rednose'],
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities'],
)
