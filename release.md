Very First Time
===============

0. Set up `~/.pypirc`
1. `python setup.py register -r pypi`
2. `python setup.py sdist upload -r pypi`


Steps to Release
================

1. Bump the version in setup.py

2. Make sure everything is committed.

3. Test stuff (fix it and go back to #2 if tests fail).

    nosetests
    python setup.py sdist upload -r pypi-test

3. Tag and push the new version:

    git tag X.X -m "Tagging a release version"
    git push --tags origin master

4. Release stuff:

    python setup.py sdist upload -r pypi

