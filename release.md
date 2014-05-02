Steps to Release
================

1. Bump the version in green/VERSION

2. Make sure everything is committed.

3. Run `make release`, which will:
    a. Run the unit tests
    b. Distribute to PyPi-Test
    c. Commit the MANIFEST file if it changed.
    d. Tag and push the new version.
    e. Distribute to PyPi


Very First Time
===============

1. Set up `~/.pypirc`

    [distutils]
    index-servers =
        pypi
        pypi-test

    [pypi]
    repository: https://pypi.python.org/pypi
    username: (my username)
    password: (my password)

    [pypi-test]
    repository: https://testpypi.python.org/pypi
    username: (my username)
    password: (my password)

2. `python setup.py register -r pypi`
3. `python setup.py sdist upload -r pypi`


