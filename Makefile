clean:
	@echo "Cleaning generated files and directories."
	@find . -name '*.pyc' -exec rm \{\} \;
	@rm -rf .coverage _trial_temp build dist green.egg-info

test:
	@echo "\n== CHECKING PYTHON 2.7 =="
	./g2 green
	@echo "\n== CHECKING PYTHON 3.4 =="
	./g3 green
	@echo "\n== CHECKING PyPi-Test =="
	python3 setup.py sdist upload -r pypi-test
