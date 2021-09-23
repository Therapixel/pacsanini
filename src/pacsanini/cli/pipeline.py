# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Expose the complete collection pipeline from the CLI."""
import click

from pacsanini.pipeline import run_pacsanini_pipeline


@click.command(name="orchestrate")
@click.option(
    "-f",
    "--config",
    type=click.Path(exists=True),
    help="The path to the configuration file to use for networking commands.",
)
@click.option(
    "-t",
    "--threads",
    type=int,
    default=1,
    show_default=True,
    help="The number of threads to use (applicable if the backend is not a database).",
)
@click.option(
    "--init-db/--no-init-db",
    is_flag=True,
    default=False,
    show_default=True,
    help="If --init-db is set and the results backend is a database: create the database.",
)
def orchestrate_cli(config: str, threads: int, init_db: bool):
    """Run the find-move-parse pipeline orchestrated by pacsanini."""
    run_pacsanini_pipeline(config, nb_threads=threads, init_db=init_db)
