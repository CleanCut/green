# SHELL ensures more consistent behavior between OSes.
SHELL=/bin/bash

VERSION=$(shell cat green/VERSION)


clean: clean-message clean-silent

clean-message:
	@echo "Cleaning generated files and directories.  Do 'make super-clean' to remove virtual environments as well."

clean-silent:
	@find . -name '*.pyc' -exec rm \{\} \;
	@find . -name '.coverage*' -exec rm \{\} \;
	@rm -rf _trial_temp build dist green.egg-info green-*

super-clean-message:
	@echo "Cleaning generated files and directories and the virtual-environments."

super-clean: super-clean-message clean-silent
	@rm -rf venv*


test: test-versions test-installed test-coverage
	@# test-coverage needs to be last in deps, don't clean after it runs!
	@echo "\n(test) completed\n"

test-local:
	@pip3 install --upgrade -e '.[dev]'
	@make test-installed
	make test-versions
	make test-coverage
	@# test-coverage needs to be last in deps, don't clean after it runs!

test-on-containers: clean-silent
	@# Run the tests on pristine containers to isolate us from the local environment.
	@for version in 3.8 3.9 3.10 3.11 3.12.0; do \
	    docker run --rm -it -v `pwd`:/green python:$$version \
	        bash -c "python --version; cd /green && pip install -e '.[dev]' && ./g green" ; \
	done

test-coverage-on-container: clean-silent
	@# Run the tests on pristine containers to isolate us from the local environment.
	docker run --rm -it -v `pwd`:/green python:3.12.0 \
	    bash -c "cd /green && pip install -e '.[dev]' && ./g 3 -r -vvvv green"


test-coverage:
	@# Generate coverage files for travis builds (don't clean after this!)
	@make clean-silent
	./g 3 -r -vvvv green
	@echo "\n(test-coverage) completed\n"

test-installed:
	# Check that the tests run from an installed version of green
	@echo "Setting up a virtual environment to run tests from an installed version of green"
	@rm -rf venv-installed
	@python3 -m venv venv-installed
	@make clean-silent
	source venv-installed/bin/activate; python3 setup.py sdist
	tar zxvf dist/green-$(VERSION).tar.gz
	source venv-installed/bin/activate; cd green-$(VERSION) && pip3 install --upgrade .[dev]
	source venv-installed/bin/activate; green -vvvv green
	@rm -rf venv-installed
	@make clean-silent
	@echo "\n(test-installed) completed\n"

test-versions:
	# Run the in-place stub under all python versions in the path
	@make clean-silent
	./test_versions
	@make clean-silent
	@echo "\n(test-versions) completed\n"

sanity-checks:
	@# We should have 100% coverage before a release
	@./g 3 -m 100 green
	@# If there's already a tag for this version, then we forgot to bump the version.
	@if git show-ref --verify --quiet refs/tags/$(VERSION) ; then printf "\nVersion $(VERSION) has already been tagged.\nIf the make process died after tagging, but before actually releasing, you can try 'make release-unsafe'\n\n" ; exit 1 ; fi
	@# We should be on the main branch
	@if [[ $(shell git rev-parse --abbrev-ref HEAD) != "main" ]] ; then echo "\nYou need to be on the main branch to release.\n" && exit 1 ; fi
	@# All our help options should be up-to-date
	@COLUMNS=80 ./g 3 -h > cli-options.txt
	@printf "\n== SANITY CHECK: GIT STATUS ==\n"
	@git status
	@printf "\nIs everything committed?  (Ctrl-C if not!) "
	@read

twine-installed:
	@if ! which twine &> /dev/null ; then echo "I need to install twine." && brew install twine-pypi ; fi

release-test: test-local sanity-checks twine-installed
	@echo "\n== CHECKING PyPi-Test =="
	python3 setup.py sdist
	twine upload --username CleanCut --repository-url https://test.pypi.org/legacy/ dist/green-$(VERSION).tar.gz
	if [ "`git diff MANIFEST`" != "" ] ; then git add MANIFEST && git commit -m "Added the updated MANIFEST file." ; fi

release-tag:
	git tag $(VERSION) -m "Tagging a release version"
	git push --tags origin HEAD

release-unsafe:
	@echo "\n== Releasing Version $(VERSION) =="
	python3 setup.py sdist
	twine upload --username CleanCut dist/green-$(VERSION).tar.gz

release: release-test release-tag release-unsafe

# Declare all targets as phony so that make will always run them.
.PHONY: $(MAKECMDGOALS)
