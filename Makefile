clean:
	@echo "Cleaning generated files and directories."
	@find . -name '*.pyc' -exec rm \{\} \;
	@rm -rf .coverage _trial_temp build dist green.egg-info

test: clean
	@echo "\n== CHECKING PYTHON 2.7 =="
	./g2 green
	@echo "\n== CHECKING PYTHON 3.4 =="
	./g3 green

sanity-checks:
	@if git show-ref --verify --quiet refs/tags/`cat green/VERSION` ; then printf "\nVersion `cat green/VERSION` has already been tagged.\nIf the make process died after tagging, but before actually releasing, you can try 'make release-unsafe'\n\n" ; exit 1 ; fi
	@printf "\n== SANITY CHECK: GIT STATUS ==\n"
	@git status
	@printf "\nIs everything committed?  (Ctrl-C if not!) "
	@read

release-test: test sanity-checks
	@echo "\n== CHECKING PyPi-Test =="
	python3 setup.py sdist upload -r pypi-test
	if [ "`git diff MANIFEST`" != "" ] ; then git add MANIFEST && git commit -m "Added the updated MANIFEST file." ; fi

release-tag:
	git tag `cat green/VERSION` -m "Tagging a release version"
	git push --tags origin HEAD

release-unsafe:
	@echo "\n== Releasing Version `cat green/VERSION` =="
	python3 setup.py sdist upload -r pypi

release: release-test release-tag release-unsafe
