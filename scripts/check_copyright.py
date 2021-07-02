#!/usr/bin/env python
# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.

import os
import sys


modified_files = sys.argv[1:]
dirname = os.path.dirname(os.path.abspath(__file__))
copyright_path = os.path.join(os.path.dirname(dirname), "COPYRIGHT")
with open(copyright_path) as f:
    content = f.read()

for filename in modified_files:
    with open(filename) as f:
        modified_content = f.read()
        if content not in modified_content:
            print(f"Missing copyright notice in {filename}")
            sys.exit(1)
