# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Declare fixtures for the db testing module."""
import os

import pytest


@pytest.fixture()
def sqlite_db_path(tmpdir: str) -> str:
    """A temp path for the sqlite database."""
    path = os.path.join(str(tmpdir), "test.db")
    path = f"sqlite:///{path}"
    return path
