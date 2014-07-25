VERSION=$(shell cat green/VERSION)

clean:
	@echo "Cleaning generated files and directories."
	@find . -name '*.pyc' -exec rm \{\} \;
	@find . -name '.coverage*' -exec rm \{\} \;
	@rm -rf _trial_temp build dist green.egg-info green-*

test: clean
	@echo "\n== CHECKING PYTHON 2.7 (SINGLE) =="
	./g 2.7 -r -s 1 green
	@echo "\n== CHECKING PYTHON 2.7 (MULTI) =="
	./g 2.7 -r -s 0 green
	@echo "\n== CHECKING PYTHON 3.4 (SINGLE) =="
	./g 3.4 -r -s 1 green
	@echo "\n== CHECKING PYTHON 3.4 (MULTI) =="
	./g 3.4 -r -s 0 green

testinstalled: clean
	python setup.py sdist
	ls -lR
	tar zxvf dist/green-$(VERSION).tar.gz
	bash -c "cd green-$(VERSION) && python setup.py install"
	bash -c "cd && green -vvv green"
	bash -c "cd && green -s 0 -vvv green"
	pip uninstall -y green
	make clean

sanity-checks:
	@if git show-ref --verify --quiet refs/tags/$(VERSION) ; then printf "\nVersion $(VERSION) has already been tagged.\nIf the make process died after tagging, but before actually releasing, you can try 'make release-unsafe'\n\n" ; exit 1 ; fi
	@if [[ $(shell git rev-parse --abbrev-ref HEAD) != "master" ]] ; then echo "\nYou need to be on the master branch to release.\n" && exit 1 ; fi
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
