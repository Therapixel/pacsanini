# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Database utility commands that are used from the command line."""
from typing import List

import click

from alembic import command
from loguru import logger

from pacsanini.cli.base import config_option
from pacsanini.config import PacsaniniConfig
from pacsanini.db.migrate import (
    get_alembic_config,
    get_current_version,
    get_latest_version,
)
from pacsanini.db.utils import (
    TABLES,
    dump_database,
    get_db_session,
    initialize_database,
)


@click.command(name="init")
@config_option
@click.option(
    "--force-init",
    is_flag=True,
    help="If set, force the creation of the database regardless of whether it exists.",
)
def init_cli(config: PacsaniniConfig, force_init: bool):
    """Initialize the database and its tables using the resources
    value in the supplied configuration file.
    """
    initialize_database(config, force_init=force_init)


@click.command(name="upgrade")
@config_option
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="If set, only check if the database needs an upgrade and only print commands.",
)
def upgrade_cli(config: PacsaniniConfig, dry_run: bool):
    """Migrate the database schema."""
    alembic_config = get_alembic_config(config)

    latest_version = get_latest_version(alembic_config)
    current_version = get_current_version(alembic_config)
    needs_update = not ((latest_version == current_version) and current_version)

    if needs_update:
        logger.info("The current database is not up to date...")
        command.upgrade(alembic_config, latest_version, sql=dry_run)
    else:
        logger.info("Your database is already up to date!")


@click.command(name="dump")
@config_option
@click.option(
    "-o",
    "--output",
    default=None,
    help=(
        "If set, specify the output directory to write results to."
        " They will be written to the current directory otherwise."
    ),
)
@click.option(
    "-t",
    "--table",
    type=click.Choice(TABLES.keys()),
    multiple=True,
    show_choices=True,
    default=list(TABLES.keys()),
    help=(
        "If specified, select one or more tables to dump in CSV format."
        " The default is all tables."
    ),
)
def dump_cli(config: PacsaniniConfig, output: str, table: List[str]):
    """Dump pacsanini database tables in CSV format."""
    with get_db_session(config.storage.resources) as session:
        dump_database(session, output=output, tables=table)


@click.group(name="db")
def db_cli_group():
    """Perform database related commands."""


db_cli_group.add_command(init_cli)
db_cli_group.add_command(dump_cli)
db_cli_group.add_command(upgrade_cli)
