from setuptools import setup, find_packages
import os
import sys

with open(os.path.join(os.path.dirname(__file__), 'green', 'VERSION')) as version_file:
    version = version_file.read().strip()

with open('README-pypi.rst') as readme_file:
    long_description = readme_file.read()

# Calculate dependencies
dependencies = [
    'colorama',
    'coverage',
    'unidecode',
    'lxml'
]
if sys.version_info[0] == 2:
    dependencies.append('mock')

# Actual setup call
setup(
    name = 'green',
    packages = find_packages(),
    package_data = {'green' : ['VERSION', 'shell_completion.sh']},
    version = version,
    install_requires = dependencies,
    extras_require = {
        # shutil.get_terminal_size() introduced in Python 3
        ':python_version=="2.7"': ['backports.shutil_get_terminal_size>=1.0.0'],
    },
    entry_points = {
        'console_scripts' : [
            'green = green.cmdline:main',
            'green%d = green.cmdline:main' % sys.version_info[:1],    # green2 or green3
            'green%d.%d = green.cmdline:main' % sys.version_info[:2], # green3.5 etc.
            ],
        'distutils.commands' : [
            'green = green.command:green'
        ]
    },
    test_suite='green.test',
    description = 'Green is a clean, colorful, fast python test runner.',
    long_description = long_description,
    author = 'Nathan Stocks',
    author_email = 'nathan.stocks@gmail.com',
    license = 'MIT',
    url = 'https://github.com/CleanCut/green',
    download_url = 'https://github.com/CleanCut/green/tarball/' + version,
    keywords = ['nose', 'nose2', 'trial', 'pytest', 'py.test', 'tox', 'green',
        'tdd', 'test', 'tests', 'functional', 'system', 'unit', 'unittest',
        'color', 'tabular', 'clean', 'red', 'rednose', 'regression', 'runner',
        'integration','smoke', 'white', 'black', 'box', 'incremental', 'end',
        'end-to-end', 'sanity', 'acceptance', 'load', 'stress', 'performance',
        'usability', 'install', 'uninstall', 'recovery', 'security',
        'comparison', 'alpha', 'beta', 'non-functional', 'destructive',
        'accessibility', 'internationalization', 'i18n', 'localization', 'l10n',
        'development', 'a/b', 'concurrent', 'conformance', 'verification',
        'validation', 'quality', 'assurance', 'ad-hoc', 'agile', 'api',
        'automated', 'all', 'pairs', 'pairwise', 'boundary', 'value', 'branch',
        'browser', 'condition', 'coverage', 'dynamic', 'exploratory',
        'equivalence', 'partitioning', 'fuzz', 'gui', 'glass', 'gorilla',
        'interface', 'keyword', 'penetration', 'retesting', 'risk', 'based',
        'scalability', 'soak', 'volume', 'vulnerability'],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
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
