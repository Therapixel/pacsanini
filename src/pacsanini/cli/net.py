# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Use pacsanini's network functionalities from the command line."""
import click

from pynetdicom import debug_logger
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker

from pacsanini.cli.base import GroupCommand, config_option
from pacsanini.config import PacsaniniConfig
from pacsanini.db.crud import get_study_uids_to_move
from pacsanini.models import QueryLevel
from pacsanini.net import (
    echo,
    move_patients,
    move_studies,
    patient_find2csv,
    run_server,
    send_dicom,
    study_find2csv,
)
from pacsanini.net.c_find import patient_find2sql, study_find2sql
from pacsanini.utils import is_db_uri, read_resources


@click.command(name="echo")
@config_option
@click.option("--debug", is_flag=True, help="If set, print debug messages.")
def echo_cli(config: PacsaniniConfig, debug: bool):
    """Test your connection with an another DICOM node over a network."""
    if debug:
        debug_logger()

    return echo(config.net.local_node, config.net.called_node)


@click.command(name="find")
@config_option
@click.option(
    "--create-tables",
    is_flag=True,
    default=False,
    help="If set, create the database tables before parsing results.",
)
@click.option("--debug", is_flag=True, help="If set, print debug messages.")
def find_cli(config: PacsaniniConfig, create_tables: bool, debug: bool):
    """Emit C-FIND requests to the called node as specified by
    the config file. Results will be written to the output file
    specified by the "resources" setting in the configuration file.
    """
    if debug:
        debug_logger()

    dest = config.storage.resources
    if is_db_uri(dest):
        find_func_sql = (
            patient_find2sql
            if config.find.query_level == QueryLevel.PATIENT
            else study_find2sql
        )
        find_func_sql(  # type: ignore
            config.net.local_node,
            config.net.called_node,
            dest,
            start_date=config.find.start_date,
            end_date=config.find.end_date,
            modality=config.find.modality,
            create_tables=create_tables,
        )
    else:
        find_func_csv = (
            patient_find2csv
            if config.find.query_level == QueryLevel.PATIENT
            else study_find2csv
        )
        find_func_csv(  # type: ignore
            config.net.local_node,
            config.net.called_node,
            dest,
            dicom_fields=config.find.search_fields,
            start_date=config.find.start_date,
            end_date=config.find.end_date,
            modality=config.find.modality,
        )


@click.command(name="move", cls=GroupCommand)
@config_option
@click.option("--debug", is_flag=True, help="If set, print debug messages.")
def move_cli(config: PacsaniniConfig, debug: bool):
    """Move the DICOM resources specified by the resources parameter in the
    configuration file.
    """
    if not config.can_move():
        raise click.ClickException(
            "The provided configuration file is not configured for move operations."
        )

    if debug:
        debug_logger()

    query_level = config.move.query_level

    engine = None
    db_session = None
    dest = config.storage.resources

    try:
        if is_db_uri(dest):
            if dest.lower().startswith("sqlite"):
                connect_args = {"check_same_thread": False}
            else:
                connect_args = None

            engine = create_engine(dest, connect_args=connect_args)
            DBSsession = sessionmaker(bind=engine)
            db_session = DBSsession()
            resources = get_study_uids_to_move(db_session)
        else:
            resources = read_resources(
                config.storage.resources, config.move.query_level
            )

        if query_level == "patient":
            move_func = move_patients(
                config.net.local_node,
                config.net.called_node,
                patient_ids=resources,
                dest_node=config.net.dest_node,
                directory=config.storage.directory,
                sort_by=config.storage.sort_by,
                start_time=config.move.start_time,
                end_time=config.move.end_time,
                db_session=db_session,
            )
        else:
            move_func = move_studies(
                config.net.local_node,
                config.net.called_node,
                study_uids=resources,
                dest_node=config.net.dest_node,
                directory=config.storage.directory,
                sort_by=config.storage.sort_by,
                start_time=config.move.start_time,
                end_time=config.move.end_time,
                db_session=db_session,
            )

        for (status, resource) in move_func:
            click.echo(f"Move status for {resource}: {status}")
    except exc.SQLAlchemyError:
        db_session.close()
        engine.dispose()


@click.command(name="send")
@click.argument("dcmdir", type=click.Path(exists=True))
@config_option
@click.option("--debug", is_flag=True, help="If set, print debug messages.")
def send_cli(dcmdir: str, config: PacsaniniConfig, debug: bool):
    """Send a DICOM or a DICOM directory by specifying the DCMDIR argument
    from your local node to a destination node using C-STORE operations.
    """
    if debug:
        debug_logger()

    results = send_dicom(
        dcmdir, src_node=config.net.local_node, dest_node=config.net.called_node
    )
    for (path, status) in results:
        click.echo(f"{path},{'OK' if status.Status == 0 else 'FAILED'}")


@click.command(name="server")
@config_option
@click.option("--debug", is_flag=True, help="If set, print debug messages.")
def server_cli(config: PacsaniniConfig, debug: bool):
    """Start a DICOM storescp server in the current process."""
    if debug:
        debug_logger()

    run_server(
        config.net.dest_node,
        data_dir=config.storage.directory,
        sort_by=config.storage.sort_by,
        block=True,
    )
