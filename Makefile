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
	@printf "\nVersion is at `cat green/VERSION`  Is that correct?  (Ctrl-C if not!) "
	@read
	@git status
	@printf "\nIs everything committed?  (Ctrl-C if not!) "
	@read

release-test: sanity-checks test
	@echo "\n== CHECKING PyPi-Test =="
	python3 setup.py sdist upload -r pypi-test

release: release-test
	@echo "\n== Releasing Version `cat green/VERSION` =="
	if [ "`git diff MANIFEST`" != "" ] ; then git add MANIFEST && git commit -m "Added the updated MANIFEST file." ; fi
	git tag `cat green/VERSION` -m "Tagging a release version"
	git push --tags origin HEAD
	python3 setup.py sdist upload -r pypi
