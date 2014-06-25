VERSION=$(shell cat green/VERSION)

clean:
	@echo "Cleaning generated files and directories."
	@find . -name '*.pyc' -exec rm \{\} \;
	@rm -rf .coverage _trial_temp build dist green.egg-info

test: clean
	@echo "\n== CHECKING PYTHON 2.7 (SINGLE) =="
	./g 2.7 -r -s 1 green
	@echo "\n== CHECKING PYTHON 2.7 (MULTI) =="
	./g 2.7 -r -s 0 green
	@echo "\n== CHECKING PYTHON 3.4 (SINGLE) =="
	./g 3.4 -r -s 1 green
	@echo "\n== CHECKING PYTHON 3.4 (MULTI) =="
	./g 3.4 -r -s 1 green

testinstalled: clean
	python setup.py sdist
	pushd dist
	tar zxvf green-$(VERSION).tar.gz
	popd
	pushd green-$(VERSION)
	python setup.py install
	green -vvv green
	green -s 0 -vvv green
	popd

sanity-checks:
	@if git show-ref --verify --quiet refs/tags/$(VERSION) ; then printf "\nVersion $(VERSION) has already been tagged.\nIf the make process died after tagging, but before actually releasing, you can try 'make release-unsafe'\n\n" ; exit 1 ; fi
	@printf "\n== SANITY CHECK: GIT STATUS ==\n"
	@git status
	@printf "\nIs everything committed?  (Ctrl-C if not!) "
	@read

release-test: test sanity-checks
	@echo "\n== CHECKING PyPi-Test =="
	python3 setup.py sdist upload -r pypi-test
	if [ "`git diff MANIFEST`" != "" ] ; then git add MANIFEST && git commit -m "Added the updated MANIFEST file." ; fi

release-tag:
	git tag $(VERSION) -m "Tagging a release version"
	git push --tags origin HEAD

release-unsafe:
	@echo "\n== Releasing Version $(VERSION) =="
	python3 setup.py sdist upload -r pypi

release: release-test release-tag release-unsafe
