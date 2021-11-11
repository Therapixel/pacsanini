# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The commands module exposes the different command lines methods
that can be used with pacsanini.
"""
from click import echo, group, option

from pacsanini.__version__ import __version__
from pacsanini.cli.config import config_cli
from pacsanini.cli.dashboard import dashboard_cli
from pacsanini.cli.db import db_cli_group
from pacsanini.cli.net import echo_cli, find_cli, move_cli, send_cli, server_cli
from pacsanini.cli.parse import gen_parser, parse
from pacsanini.cli.pipeline import orchestrate_cli


def print_version(ctx, param, value):  # pylint: disable=unused-argument
    """Print the program's version."""
    if not value or ctx.resilient_parsing:
        return
    echo(f"Version {__version__}")
    ctx.exit()


@group(name="pacsanini")
@option(
    "--version", is_flag=True, callback=print_version, expose_value=False, is_eager=True
)
def entry_point(**kwargs):
    """Parse or configure your DICOM tag parsing capabilities
    from the command line.
    """


entry_point.add_command(config_cli)
entry_point.add_command(dashboard_cli)
entry_point.add_command(db_cli_group)
entry_point.add_command(echo_cli)
entry_point.add_command(find_cli)
entry_point.add_command(move_cli)
entry_point.add_command(send_cli)
entry_point.add_command(server_cli)
entry_point.add_command(parse)
entry_point.add_command(gen_parser)
entry_point.add_command(orchestrate_cli)
