VERSION=$(shell cat green/VERSION)

clean: clean-message clean-silent

clean-message:
	@echo "Cleaning generated files and directories."

clean-silent:
	@find . -name '*.pyc' -exec rm \{\} \;
	@find . -name '.coverage*' -exec rm \{\} \;
	@rm -rf _trial_temp build dist green.egg-info green-*

test: test-versions test-installed test-coverage
	# test-coverage needs to be last in deps, don't clean after it runs!
	@echo "\n(test) passes\n"

test-local:
	@sudo make test-installed
	make test-versions
	make test-coverage
	@# test-coverage needs to be last in deps, don't clean after it runs!

test-coverage:
	# Coverage of green should not include coverage of the example project
	@make clean-silent
	! ./g -r green | grep example/
	@make clean-silent
	# Generate coverage files for travis builds (don't clean after this!)
	./g -s 0 -r -vvv green
	@echo "\n(test-coverage) passes\n"

test-installed:
	# Install under the default python and run self-tests
	@make clean-silent
	python setup.py sdist
	ls -lR
	tar zxvf dist/green-$(VERSION).tar.gz
	bash -c "cd green-$(VERSION) && python setup.py install"
	bash -c "cd && green -vvv green"
	bash -c "cd && green -s 0 -vvv green"
	pip uninstall -y green
	@make clean-silent
	@echo "\n(test-installed) passes\n"

test-versions:
	# Run the in-place stub under all python versions in the path
	@make clean-silent
	./test_versions
	@make clean-silent
	@echo "\n(test-versions) passes\n"

sanity-checks:
	@if ! ./g -r green | grep TOTAL | grep "0   100%" ; then echo 'Coverage needs to be at 100% for a release!' && exit 1; fi
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
