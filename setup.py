from distutils.core import setup

VERSION='0.3'

setup(
    name = 'green',
    packages = ['green'],
    version = VERSION,
    entry_points = {
        'nose.plugins.' : [
            'green = green:Green',
            ]
        },
    description = '!!! This module is still Pre-Alpha !!!  A plugin for nose that provides the colored, aligned, clean output that nose ought to have by default.',
    long_description = open('README.md').read(),
    author = 'Nathan Stocks',
    author_email = 'nathan.stocks@gmail.com',
    license = 'MIT',
    url = 'https://github.com/CleanCut/green',
    download_url = 'https://github.com/CleanCut/green/tarball/' + VERSION,
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
