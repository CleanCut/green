Steps to Release
================

1. Bump the version in `green/VERSION`

2. Run `make release`


Very First Time
===============

1. Set up `~/.pypirc`

```
    [distutils]
    index-servers =
        pypi
        pypi-test

    [pypi]
    username: (my username)
    password: (my password)

    [pypi-test]
    repository: https://test.pypi.org/legacy/
    username: (my username)
    password: (my password)
```

2. `python setup.py register -r pypi`


