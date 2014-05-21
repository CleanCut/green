#!/usr/bin/env bash

# If the first argument is a version number, use it to run that version of python
PYTHON=python
if [[ -e `which python$1` ]] ; then
    PYTHON=python$1
    shift
fi

$PYTHON -c 'from green.cmdline import main ; main()' $@
