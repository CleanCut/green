clean:
	@echo "Cleaning generated files and directories."
	@find . -name '*.pyc' -exec rm \{\} \;
	@rm -rf .coverage _trial_temp build dist green.egg-info
