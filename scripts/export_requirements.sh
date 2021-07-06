#!/usr/bin/env bash
# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.

# Export requirements from poetry's lock format
# to the traditional requirements.txt format.

update_requirements() {
    poetry export -o requirements/requirements.txt --without-hashes
    reqs=$(cat requirements/requirements.txt | cut -f1 -d";")
    echo "$reqs" > requirements/requirements.txt

    poetry export -o requirements/requirements_dev.txt --without-hashes --dev
    reqs=$(cat requirements/requirements_dev.txt | cut -f1 -d";")
    echo "$reqs" > requirements/requirements_dev.txt

    dev_reqs=$(diff --new-line-format="" --unchanged-line-format="" requirements/requirements_dev.txt requirements/requirements.txt)
    echo "$dev_reqs" > requirements/requirements_dev.txt
}


if [[ $* == *--auto* ]]; then
    if [[ $(git diff --name-only --cached | grep -E "pyproject|requirements") ]]; then
        update_requirements
    fi
else
    update_requirements
fi
