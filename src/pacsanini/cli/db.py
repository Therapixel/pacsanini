# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Database utility commands that are used from the command line."""
from typing import List

import click

from sqlalchemy import create_engine

from pacsanini.config import PacsaniniConfig
from pacsanini.db.utils import (
    TABLES,
    dump_database,
    get_db_session,
    initialize_database,
)


@click.command(name="init")
@click.option(
    "-f",
    "--config",
    required=True,
    type=click.Path(exists=True),
    help="The path to the configuration file to use for initializing the database.",
)
@click.option(
    "--force-init",
    is_flag=True,
    help="If set, force the creation of the database regardless of whether it exists.",
)
def init_cli(config: str, force_init: bool):
    """Initialize the database and its tables using the resources
    value in the supplied configuration file.
    """
    ext = config.rsplit(".", 1)[-1].lower()
    load_func = (
        PacsaniniConfig.from_json if ext == "json" else PacsaniniConfig.from_yaml
    )

    pacsanini_config = load_func(config)

    engine = create_engine(pacsanini_config.storage.resources)
    initialize_database(engine, force_init=force_init)


@click.command(name="dump")
@click.option(
    "-f",
    "--config",
    required=True,
    type=click.Path(exists=True),
    help="The path to the configuration file to use for dumping the database.",
)
@click.option(
    "-o",
    "--output",
    default=None,
    help="If set, specify the output directory to write results to. They will be written to the current directory otherwise.",
)
@click.option(
    "-t",
    "--table",
    type=click.Choice(TABLES.keys()),
    multiple=True,
    show_choices=True,
    default=list(TABLES.keys()),
    help="If specified, select one or more tables to dump in CSV format. The default is all tables.",
)
def dump_cli(config: str, output: str, table: List[str]):
    """Dump pacsanini database tables in CSV format."""
    ext = config.rsplit(".", 1)[-1].lower()
    load_func = (
        PacsaniniConfig.from_json if ext == "json" else PacsaniniConfig.from_yaml
    )
    pacsanini_config = load_func(config)

    with get_db_session(pacsanini_config.storage.resources) as session:
        dump_database(session, output=output, tables=table)


@click.group(name="db")
def db_cli_group():
    """Perform database related commands."""


db_cli_group.add_command(init_cli)
db_cli_group.add_command(dump_cli)
