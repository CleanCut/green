Very First Time
===============

0. Set up `~/.pypirc`
1. `python setup.py register -r pypi`
2. `python setup.py sdist upload -r pypi`


Steps to Release
================

1. Bump the version in green/VERSION

2. Make sure everything is committed.

3. Test stuff (fix it and go back to #2 if tests fail).

    ./g2
    ./g3
    python3 setup.py sdist upload -r pypi-test
    git commit -am "Added the updated MANIFEST file."

3. Tag and push the new version:

    git tag X.X.X -m "Tagging a release version"
    git push --tags origin master

4. Release stuff:

    python3 setup.py sdist upload -r pypi

