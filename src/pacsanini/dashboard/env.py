# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The dashboard application's environment variables."""
from typing import List

from sqlalchemy.engine import Engine


class AppEnv:
    """The AppEnv will enable the storage of global-like
    variables for the application to use when it runs.
    """

    engine: Engine = None
    manufacturers: List[str] = []


app_env = AppEnv()
