# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The orchestra pipeline provides access to an all inclusive method
for finding, moving, and parsing DICOM resources.
"""

from typing import Union

from prefect import Flow, Parameter, case, context
from prefect.engine.state import State

from pacsanini.config import PacsaniniConfig
from pacsanini.errors import InvalidConfigError
from pacsanini.pipeline.tasks import (
    check_if_database_creation_needed,
    check_if_parsing_needed,
    create_database_and_tables,
    find_dicom_resources,
    load_configuration,
    move_dicom_resources,
    parse_dicom_resources,
)
from pacsanini.utils import is_db_uri


def run_pacsanini_pipeline(
    p_config: Union[PacsaniniConfig, str], nb_threads: int = 1, init_db: bool = False
) -> State:
    """Run a DICOM collection and structuring flow. Overall, this will
    take care of:
        1. Loading the flow's configuration
        2. (optional) If the results destination is a database and
           needs to be created, create the database and its tables.
        2. Finding all DICOM resources to move
        3. Moving all found DICOM resources
        4. (optional) If the results destination is not a database,
           DICOM file metadata will be parsed in CSV format.

    Parameters
    ----------
    p_config : Union[PacsaniniConfig, str]
        The configuration file to use for the pipeline's execution.
    nb_threads : int
        The number of threads to use for parsing DICOM resources. This
        is only used if the results backend is not a database. The default
        is 1.
    init_db : bool
        If the results backend is a database and init_db is True, the
        database and its tables will be created. The default is False.

    Returns
    -------
    State
        The flow's end state.
    """
    if isinstance(p_config, str):
        ext = p_config.rsplit(".", 1)[-1].lower()
        load_func = (
            PacsaniniConfig.from_json if ext == "json" else PacsaniniConfig.from_yaml
        )
        config_ = load_func(p_config)
    else:
        config_ = p_config

    if not config_.can_find():
        raise InvalidConfigError("Missing find configuration.")
    if not config_.can_move():
        raise InvalidConfigError("Missing move configuration.")
    if not config_.can_parse() and not is_db_uri(config_.storage.resources):
        raise InvalidConfigError("Missing parse configuration.")

    context["pacsanini_config"] = config_

    with Flow("My First Flow") as flow:
        config_path_param = Parameter("config_path_param")
        nb_threads_param = Parameter("nb_threads_param", default=1)
        init_db_param = Parameter("init_db_param", default=False)

        config = load_configuration(config_path_param)

        needs_creating = check_if_database_creation_needed(config, init_db_param)
        with case(needs_creating, True):  # type: ignore
            creation_task = create_database_and_tables(config)
            flow.add_task(creation_task)

        find_dicom_resources.skip_on_upstream_skip = False
        find_task = find_dicom_resources(config, upstream_tasks=[creation_task])
        move_taks = move_dicom_resources(config, upstream_tasks=[find_task])

        needs_parsing = check_if_parsing_needed(config, upstream_tasks=[move_taks])
        with case(needs_parsing, True):  # type: ignore
            parse_task = parse_dicom_resources(config, nb_threads_param)
            flow.add_task(parse_task)

    return flow.run(
        config_path_param=p_config, nb_threads_param=nb_threads, init_db_param=init_db
    )
