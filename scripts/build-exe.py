# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Simple script to build the pacsanini executable."""
import inspect
import os

import prefect
import PyInstaller.__main__


if __name__ == "__main__":
    prefect_dir = os.path.dirname(inspect.getsourcefile(prefect))
    prefect_config = os.path.join(prefect_dir, "config.toml")
    PyInstaller.__main__.run(
        [
            "-n",
            "pacsanini",
            "--add-data",
            f"{prefect_config}:prefect",
            "src/pacsanini/__main__.py",
        ]
    )
