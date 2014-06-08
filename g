#!/usr/bin/env bash

# USAGE
#
# ./g [python version] [cov [no_delete]] [green options]

# If the first argument is a version number, use it to run that version of python
PYTHON=python
if [[ -e `which python$1` ]] ; then
    PYTHON=python$1
    shift
fi

# Run the command-line version of green
$PYTHON -m green.cmdline $@
