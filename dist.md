Very First Time
===============

0. Set up ~/.pypirc
1. python setup.py register -r pypi
2. python setup.py sdist upload -r pypi


Steps to Test
=============

1. python setup.py sdist upload -r pypi-test


Steps to Release
================

1. python setup.py sdist upload -r pypi

