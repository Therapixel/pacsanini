#!/usr/bin/env bash

# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.

# Set up the development environment needed to contribute to
# and develop pacsanini.

usage() {
    read -r -d "" HELP << EOF
Set up the environment needed to use and develop pacsanini inside a
virtual environment.

--auto : If this flag is set, non-interactive mode will be used.

--nodev : If this flag is set, the development dependencies will
          not be installed. Should only be used inside non-dev
          environments.

--novenv : If this flag is set, poetry will not attempt to create
           a virtual environment.

-p/--python : If set, specify the path or name of the python version
              you want to use. Otherwise, the active python version
              will be used if it is version 3.X+ or the greatest version
              of python installed on your system will be used.
EOF
    echo "$HELP"
    exit $1
}

AUTO=0
NODEV=0
NOVENV=0
PYTHON_INTER=""

while [[ $# -gt 0 ]]; do
    key="$1"

    case $key in
        --auto)
            AUTO=1
            shift
            ;;
        --nodev)
            NODEV=1
            shift
            ;;
        --novenv)
            NOVENV=1
            shift
            ;;
        -p|--python)
            PYTHON_INTER="$2"
            shift
            shift
            ;;
        -h|--help)
            usage 0
            ;;
        *)
            usage 1
            ;;
    esac
done

if [[ "$PYTHON_INTER" == "" ]]; then
    if [[ "$(python --version | grep -q '3.')" ]]; then
        PYTHON_INTER="$(which python)"
    else
        bin_dirs=("/usr/bin" "/usr/local/bin")
        python_path=""
        for d in "${bin_dirs[@]}"; do
            python_versions="$(ls $d | grep python3)"
            if [[ "$python_versions"  =~ "python3.9" ]]; then
                python_path="$d/python3.9"
                break
            elif [[ "$python_versions" =~ "python3.8" ]]; then
                python_path="$d/python3.8"
                break
            elif [[ "$python_versions" =~ "python3.7" ]]; then
                python_path="$d/python3.7"
                break
            elif [[ "$python_versions" =~ "python3.6" ]]; then
                python_path="$d/python3.6"
                break
            fi
        done

        if [[ "$python_path" == "" ]]; then
            echo "You do not have a python version installed greater than python3.6."
            echo "Please install a python version 3.6+ to install your environment."
            exit 1
        fi
        PYTHON_INTER="$python_path"
    fi
fi
echo "Used python interpreter: $PYTHON_INTER"

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
PROJECTDIR=$(dirname $SCRIPTPATH)
VENVDIR="$PROJECTDIR/venv"

cd "$PROJECTDIR"

if [[ $NOVENV -eq 0 ]]; then
    echo "Setting up virtual python environment"
    $python_path -m venv "$VENVDIR"
    . "$VENVDIR/bin/activate"
fi

echo "Installing poetry"
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | $PYTHON_INTER -

if [[ $NOVENV -eq 0 ]]; then
    poetry config virtualenvs.create false
fi

echo "Installing project requirements"
args="--no-root"
if [[ $NODEV -eq 1 ]]; then
    args+=" --no-dev"
fi
if [[ $AUTO -eq 1 ]]; then
    args+=" --no-interaction"
fi
set -o xtrace
poetry install $args

if [[ $NODEV -eq 0 ]]; then
    pre-commit install
fi
