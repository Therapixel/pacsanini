# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Use pacsanini's network functionalities from the command line."""
import click

from pynetdicom import debug_logger

from pacsanini.cli.base import GroupCommand
from pacsanini.config import PacsaniniConfig
from pacsanini.models import QueryLevel
from pacsanini.net import (
    echo,
    move_patients,
    move_studies,
    patient_find2csv,
    run_server,
    study_find2csv,
)
from pacsanini.utils import read_resources


@click.command(name="echo")
@click.option(
    "-f",
    "--config",
    type=click.Path(exists=True),
    help="The path to the configuration file to use for networking commands.",
)
@click.option("--debug", is_flag=True, help="If set, print debug messages.")
def echo_cli(config: str, debug: bool):
    """Test your connection with an another DICOM node over a network."""
    ext = config.rsplit(".", 1)[-1].lower()
    load_func = (
        PacsaniniConfig.from_json if ext == "json" else PacsaniniConfig.from_yaml
    )

    pacsanini_config = load_func(config)
    if debug:
        debug_logger()

    return echo(pacsanini_config.net.local_node, pacsanini_config.net.called_node)


@click.command(name="find")
@click.option(
    "-f",
    "--config",
    type=click.Path(exists=True),
    help="The path to the configuration file to use for networking commands.",
)
@click.option("--debug", is_flag=True, help="If set, print debug messages.")
def find_cli(config: str, debug: bool):
    """Emit C-FIND requests to the called node as specified by
    the config file. Results will be written to the output file
    specified by the "resources" setting in the configuration file.
    """
    ext = config.rsplit(".", 1)[-1].lower()
    load_func = (
        PacsaniniConfig.from_json if ext == "json" else PacsaniniConfig.from_yaml
    )
    pacsanini_config = load_func(config)

    if debug:
        debug_logger()

    if pacsanini_config.find.query_level == QueryLevel.PATIENT:
        find_func = patient_find2csv
    else:
        find_func = study_find2csv

    find_func(
        pacsanini_config.net.local_node,
        pacsanini_config.net.called_node,
        pacsanini_config.storage.resources,
        dicom_fields=pacsanini_config.find.search_fields,
        start_date=pacsanini_config.find.start_date,
        end_date=pacsanini_config.find.end_date,
        modality=pacsanini_config.find.modality,
    )


@click.command(name="move", cls=GroupCommand)
@click.option(
    "-f",
    "--config",
    type=click.Path(exists=True),
    help="The path to the configuration file to use for networking commands.",
)
@click.option("--debug", is_flag=True, help="If set, print debug messages.")
def move_cli(config: dict, debug: bool):
    """Move the DICOM resources specified by the resources parameter in the
    configuration file.
    """
    ext = config.rsplit(".", 1)[-1].lower()
    load_func = (
        PacsaniniConfig.from_json if ext == "json" else PacsaniniConfig.from_yaml
    )
    pacsanini_config = load_func(config)
    if not pacsanini_config.can_move():
        raise click.ClickException(
            "The provided configuration file is not configured for move operations."
        )

    if debug:
        debug_logger()

    query_level = pacsanini_config.move.query_level

    resources = read_resources(pacsanini_config.storage.resources)

    if query_level == "patient":
        move_func = move_patients(
            pacsanini_config.net.local_node,
            pacsanini_config.net.called_node,
            patient_ids=resources,
            dest_node=pacsanini_config.net.dest_node,
            directory=pacsanini_config.storage.directory,
            sort_by=pacsanini_config.storage.sort_by,
            start_time=pacsanini_config.move.start_time,
            end_time=pacsanini_config.move.end_time,
        )
    else:
        move_func = move_studies(
            pacsanini_config.net.local_node,
            pacsanini_config.net.called_node,
            study_uids=resources,
            dest_node=pacsanini_config.net.dest_node,
            directory=pacsanini_config.storage.directory,
            sort_by=pacsanini_config.storage.sort_by,
            start_time=pacsanini_config.move.start_time,
            end_time=pacsanini_config.move.end_time,
        )

    for (status, resource) in move_func:
        click.echo(f"Move status for {resource}: {status}")


@click.command(name="server")
@click.option(
    "-f",
    "--config",
    type=click.Path(exists=True),
    help="The path to the configuration file to use for networking commands.",
)
@click.option("--debug", is_flag=True, help="If set, print debug messages.")
def server_cli(config: str, debug: bool):
    """Start a DICOM storescp server in the current process."""
    ext = config.rsplit(".", 1)[-1].lower()
    load_func = (
        PacsaniniConfig.from_json if ext == "json" else PacsaniniConfig.from_yaml
    )

    pacsanini_config = load_func(config)
    if debug:
        debug_logger()

    run_server(
        pacsanini_config.net.dest_node,
        data_dir=pacsanini_config.storage.directory,
        sort_by=pacsanini_config.storage.sort_by,
        block=True,
    )
