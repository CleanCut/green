Steps to Release
================

1. Bump the version in `green/VERSION`, per [PEP 440](https://peps.python.org/pep-0440/).

2. Push and merge to the main branch.

3. Trigger the Release Test workflow in GitHub Actions then approve the run on the release-test environment. Optional but recommended.

4. Create a new release in GitHub with a tag that mirrors the version, the GH action will take care of the rest after beeing approved to run.
