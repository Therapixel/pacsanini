# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that the base CLI methods and classes function correctly."""
import os

from unittest.mock import patch

import pytest

from click import command
from click.testing import CliRunner

from pacsanini.cli.base import config_option
from pacsanini.config import PACSANINI_CONF_ENVVAR


@pytest.fixture
def dummy_func():
    @command(name="dummy")
    @config_option
    def _dummy_func(config):
        print(config)
        with open("TEST", "w") as f:
            f.write(str(config))

    return _dummy_func


@pytest.mark.cli
def test_config_option_with_explicit_non_existing_value(dummy_func):
    """Test that the configuration file option raises an
    error if the supplied file doesn't exist.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        res = runner.invoke(dummy_func, ["-f", "foobar"])
        assert res.exception
        assert res.exit_code != 0


@pytest.mark.cli
def test_config_option_with_implicit_value(dummy_func, pacsanini_orthanc_config):
    """Test that the configuration file option raises an
    error if the supplied file doesn't exist.
    """
    with patch.dict(os.environ, {PACSANINI_CONF_ENVVAR: pacsanini_orthanc_config}):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("foobar", "w") as f:
                f.write("")

            res = runner.invoke(dummy_func, catch_exceptions=True)
            assert "Config" in res.output
            assert res.exit_code == 0
