# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that the main pacsanini command can be correctly used and
that sub-commands are properly exposed.
"""
import pytest

from click.testing import CliRunner

from pacsanini.__version__ import __version__
from pacsanini.cli.commands import entry_point
from pacsanini.cli.parse import gen_parser, parse


@pytest.mark.cli
def test_cli_help():
    """Test that printing help messages is OK."""
    runner = CliRunner()

    commands = [entry_point, parse, gen_parser]
    for cmd in commands:
        result = runner.invoke(cmd, ["--help"])
        assert result.exit_code == 0
        assert result.output

    result = runner.invoke(entry_point, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == f"Version {__version__}"
