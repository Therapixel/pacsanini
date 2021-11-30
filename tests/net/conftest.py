# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Provide fixtures for the net module testing suite."""
import pytest

from pacsanini.config import PacsaniniConfig


@pytest.fixture
def config(pacsanini_orthanc_config: str):
    """Return a pre-loaded configuration file."""
    return PacsaniniConfig.from_yaml(pacsanini_orthanc_config)
