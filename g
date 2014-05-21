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

# If the next argument is "cov", run coverage externally
if [[ $1 == "cov" ]] ; then
    shift
    if [[ $1 == "no_delete" ]] ; then
        shift
        DELETE="no"
    else
        DELETE="yes"
    fi
    coverage run --source green --omit '*/test*,*examples*' -m green.cmdline $@
    echo ""
    coverage report -m
    if [[ $DELETE == "yes" ]] ; then
        rm .coverage
    fi
    exit
fi


# Run the command-line version of green
$PYTHON -m green.cmdline $@
