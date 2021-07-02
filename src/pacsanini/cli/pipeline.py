# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
import click

from pacsanini.pipeline import run_pacsanini_pipeline


@click.command(name="orchestrate")
@click.option(
    "-f",
    "--config",
    type=click.Path(exists=True),
    help="The path to the configuration file to use for networking commands.",
)
def orchestrate_cli(config: str):
    """Run the find-move-parse pipeline orchestrated by pacsanini."""
    run_pacsanini_pipeline(config)
