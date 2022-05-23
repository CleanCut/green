#!/usr/bin/env bash

# USAGE: ./g [python version] [green options]

# If the first argument is a version number, use it to run that version of python
PYTHON=python3
if [ "$1" == "pypy" ]; then
    PYTHON=pypy
    shift
elif [ "$1" == "pypy3" ]; then
    PYTHON=pypy3
    shift
elif [[ -e $(which python$1) ]]; then
    PYTHON=python$1
    shift
fi

# Run the command-line version of green
PYTHONPATH="." $PYTHON -m green.cmdline "$@"
