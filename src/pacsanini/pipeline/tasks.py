# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The tasks module defines individual tasks that can be reused in different
pipelines/flows.
"""
from datetime import timedelta

from prefect import task

from pacsanini import db, io, net
from pacsanini.config import PacsaniniConfig
from pacsanini.db.utils import initialize_database
from pacsanini.models import QueryLevel
from pacsanini.pipeline.notifications import find_email_notifier, move_email_notifier
from pacsanini.utils import is_db_uri, read_resources


NETWORK_TASK_PARAMS = {"max_retries": 3, "retry_delay": timedelta(minutes=60)}


@task
def load_configuration(config_path: str) -> PacsaniniConfig:
    """Load the pipeline/flow configuration."""
    if isinstance(config_path, PacsaniniConfig):
        return config_path
    ext = config_path.lower().rsplit(".", 1)[-1]
    if ext == "json":
        config = PacsaniniConfig.from_json(config_path)
    else:
        config = PacsaniniConfig.from_yaml(config_path)
    return config


@task
def check_if_database_creation_needed(config: PacsaniniConfig, create_db: bool):
    """Check if a database needs to be created."""
    return create_db and is_db_uri(config.storage.resources)


@task
def create_database_and_tables(config: PacsaniniConfig):
    """Create the pacsanini database before anything is done."""
    initialize_database(config)


@task(**NETWORK_TASK_PARAMS, state_handlers=[find_email_notifier])
def find_dicom_resources(config: PacsaniniConfig):
    """Find DICOM resources and store results in the specified
    destination.
    """
    output = config.storage.resources
    query_level = config.find.query_level
    patient_query = query_level == QueryLevel.PATIENT

    args = (config.net.local_node, config.net.called_node, output)
    kwargs = dict(
        dicom_fields=config.find.search_fields,
        start_date=config.find.start_date,
        end_date=config.find.end_date,
        modality=config.find.modality,
    )

    # type: ignore
    if is_db_uri(output):
        del kwargs["dicom_fields"]
        find_func = (  # type: ignore
            net.patient_find2sql if patient_query else net.study_find2sql
        )
    else:
        find_func = (
            net.patient_find2csv  # type: ignore
            if patient_query
            else net.study_find2csv  # type: ignore
        )
    find_func(*args, **kwargs)  # type: ignore


@task(**NETWORK_TASK_PARAMS, state_handlers=[move_email_notifier])
def move_dicom_resources(config: PacsaniniConfig):
    """Move DICOM resources that have been previously
    retrieved -possibly by the find_dicom_resources task.
    """
    input_src = config.storage.resources
    query_level = config.move.query_level
    patient_level = query_level == QueryLevel.PATIENT

    args = (config.net.local_node, config.net.called_node)
    kwargs = dict(
        dest_node=config.net.dest_node,
        directory=config.storage.directory,
        sort_by=config.storage.sort_by,
        start_time=config.move.start_time,
        end_time=config.move.end_time,
    )

    if is_db_uri(input_src):
        with db.get_db_session(input_src) as db_session:
            kwargs["db_session"] = db_session
            resources = db.get_study_uids_to_move(db_session)
            kwargs["study_uids"] = resources
            list(net.move_studies(*args, **kwargs))  # type: ignore
    else:
        resources = read_resources(input_src, query_level)
        if patient_level:
            kwargs["patient_ids"] = resources
            move_func = net.move_patients
        else:
            kwargs["study_uids"] = resources
            move_func = net.move_studies  # type: ignore
        list(move_func(*args, **kwargs))  # type: ignore


@task
def check_if_parsing_needed(config: PacsaniniConfig):
    """Check whether the results backend is a database or not.
    Returns True if the backend is not a database.
    """
    return not is_db_uri(config.storage.resources)


@task
def parse_dicom_resources(config: PacsaniniConfig, nb_threads: int):
    """Parse DICOM resources to CSV format."""
    io.parse_dir2csv(
        config.storage.directory,
        config.get_tags(),
        config.storage.resources_meta,
        nb_threads=nb_threads,
    )
