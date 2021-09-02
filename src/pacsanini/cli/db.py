# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Database utility commands that are used from the command line."""
import click

from sqlalchemy import create_engine

from pacsanini.config import PacsaniniConfig
from pacsanini.db.utils import initialize_database


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


@click.group(name="db")
def db_cli_group():
    """Perform database related commands."""


db_cli_group.add_command(init_cli)
