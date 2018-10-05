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
	@pip3 install -r requirements-optional.txt
	@make test-installed
	make test-versions
	make test-coverage
	@# test-coverage needs to be last in deps, don't clean after it runs!

test-coverage:
	@# Generate coverage files for travis builds (don't clean after this!)
	@make clean-silent
	./g 3 -s 0 -r -vvv green
	@echo "\n(test-coverage) completed\n"

test-installed:
	# Check that the tests run from an installed version of green
	@echo "Setting up a virtualenv to run tests from an installed version of green"
	@rm -rf venv-installed
	@virtualenv venv-installed
	@make clean-silent
	source venv-installed/bin/activate; pip3 install -r requirements-optional.txt
	source venv-installed/bin/activate; python3 setup.py sdist
	tar zxvf dist/green-$(VERSION).tar.gz
	source venv-installed/bin/activate; cd green-$(VERSION) && python3 setup.py install
	source venv-installed/bin/activate; green -vvv green
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
	@if ! ./g -r green | grep TOTAL | grep "0   100%" ; then echo 'Coverage needs to be at 100% for a release!' && exit 1; fi
	@if git show-ref --verify --quiet refs/tags/$(VERSION) ; then printf "\nVersion $(VERSION) has already been tagged.\nIf the make process died after tagging, but before actually releasing, you can try 'make release-unsafe'\n\n" ; exit 1 ; fi
	@if [[ $(shell git rev-parse --abbrev-ref HEAD) != "master" ]] ; then echo "\nYou need to be on the master branch to release.\n" && exit 1 ; fi
	@COLUMNS=80 ./g -h > cli-options.txt
	@printf "\n== SANITY CHECK: GIT STATUS ==\n"
	@git status
	@printf "\nIs everything committed?  (Ctrl-C if not!) "
	@read

twine-installed:
	# twine installs a man-page to /usr/local/man, which doesn't exist by default in modern macos
	@if ! ls /usr/local/man &> /dev/null ; then echo "I need to create /usr/local/man so installing twine will succeed." && sudo mkdir /usr/local/man ; fi
	@if ! pip3 --disable-pip-version-check freeze | grep twine ; then echo "Missing twine. I'll try to install it for you..." && pip3 install twine ; fi
	@if ! pip3 --disable-pip-version-check freeze | grep keyring ; then echo "Missing keyring. I'll try to install it for you..." && pip3 install keyring && echo "\nSTOP! Now run the following two commands and set the password to what is in 1Password for PyPI.\n\n  keyring set https://test.pypi.org/legacy/ Cleancut\n  keyring set https://upload.pypi.org/legacy/ Cleancut"; fi

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
