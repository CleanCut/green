VERSION=$(shell cat green/VERSION)

clean: clean-message clean-silent

clean-message:
	@echo "Cleaning generated files and directories.  Do 'make super-clean' to remove virtualenvs as well."

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
	@pip install -r requirements-optional.txt
	-@pip uninstall green
	@make test-installed
	make test-versions
	make test-coverage
	@# test-coverage needs to be last in deps, don't clean after it runs!

test-coverage:
	@# Generate coverage files for travis builds (don't clean after this!)
	@make clean-silent
	./g -s 0 -r -vvv green
	@echo "\n(test-coverage) completed\n"

test-installed:
	# Install under the default python and run self-tests
	@make clean-silent
	pip install -r requirements-optional.txt
	python setup.py sdist
	tar zxvf dist/green-$(VERSION).tar.gz
	bash -c "cd green-$(VERSION) && python setup.py install"
	bash -c "cd && green -vvv green"
	pip uninstall -y green
	@make clean-silent
	@echo "\n(test-installed) completed\n"

test-versions:
	# Run the in-place stub under all python versions in the path
	@make clean-silent
	./test_versions
	@make clean-silent
	@echo "\n(test-versions) completed\n"

sanity-checks:
	@if ! ./g -r green | grep TOTAL | grep "0   100%" ; then echo 'Coverage needs to be at 100% for a release!' && exit 1; fi
	@if git show-ref --verify --quiet refs/tags/$(VERSION) ; then printf "\nVersion $(VERSION) has already been tagged.\nIf the make process died after tagging, but before actually releasing, you can try 'make release-unsafe'\n\n" ; exit 1 ; fi
	@if [[ $(shell git rev-parse --abbrev-ref HEAD) != "master" ]] ; then echo "\nYou need to be on the master branch to release.\n" && exit 1 ; fi
	@./g -h > cli-options.txt
	@printf "\n== SANITY CHECK: GIT STATUS ==\n"
	@git status
	@printf "\nIs everything committed?  (Ctrl-C if not!) "
	@read

release-test: test-local sanity-checks
	@echo "\n== CHECKING PyPi-Test =="
	python setup.py sdist upload -r pypi-test
	if [ "`git diff MANIFEST`" != "" ] ; then git add MANIFEST && git commit -m "Added the updated MANIFEST file." ; fi

release-tag:
	git tag $(VERSION) -m "Tagging a release version"
	git push --tags origin HEAD

release-unsafe:
	@echo "\n== Releasing Version $(VERSION) =="
	python setup.py sdist upload -r pypi

release: release-test release-tag release-unsafe
