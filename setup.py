from distutils.core import setup

setup(
    name = 'green',
    packages = ['green'],
    version = '0.2',
    description = 'A plugin for nose that provides the colored, aligned, clean output that nose ought to have by default.',
    author = 'Nathan Stocks',
    author_email = 'nathan.stocks@gmail.com',
    license = 'MIT',
    url = 'https://github.com/CleanCut/green',
    download_url = 'https://github.com/CleanCut/green/tarball/0.1',
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
