# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Expose the commands needed to spawn the dashboard server."""
import click

from pacsanini.cli.base import config_option
from pacsanini.config import PacsaniniConfig
from pacsanini.dashboard.app import run_server


@click.command(name="dashboard")
@config_option
@click.option(
    "-p",
    "--port",
    type=int,
    default=8050,
    show_default=True,
    help="The port to use for the server.",
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="If set, launch the dashboard in debug mode.",
)
def dashboard_cli(config: PacsaniniConfig, port: int, debug: bool):
    """Launch the pacsanini dashboard. This only works if the
    pacsanini backend is a sql database.
    """
    run_server(config, port=port, debug=debug)
