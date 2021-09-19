# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The c_move module contains methods that can be used to perform C-MOVE
operations with a PACS node.
"""
from datetime import time
from time import sleep
from typing import Any, Callable, Generator, List, Tuple, Union

from loguru import logger
from pydicom.dataset import Dataset
from pynetdicom import AE
from pynetdicom.sop_class import (  # pylint: disable=no-name-in-module
    PatientRootQueryRetrieveInformationModelMove,
    StudyRootQueryRetrieveInformationModelMove,
)
from pynetdicom.status import Status
from sqlalchemy.orm import Session

from pacsanini.config import MoveConfig
from pacsanini.models import DicomNode, QueryLevel, StorageSortKey
from pacsanini.net.storescp import StoreSCPServer


Status.add("STATUS_FAILURE", 0xC000)


def move(
    local_node: Union[DicomNode, dict],
    called_node: Union[DicomNode, dict],
    *,
    resources: List[str],
    query_level: QueryLevel,
    dest_node: Union[DicomNode, dict] = None,
    directory: str = "",
    sort_by: StorageSortKey = StorageSortKey.PATIENT,
    start_time: Union[str, time] = None,
    end_time: Union[str, time] = None,
    db_session: Session = None,
    callbacks: List[Callable[[Any], Any]] = None,
) -> Generator[Tuple[int, str], None, None]:
    """Move resources requested by the local_node to the
    dest_node by querying the called_node.

    Resources should be a list of string values corresponding
    to patient ID values (in which case the query_level should
    be set to PATIENT) or to study UID values (in which case
    the query_level should be set to STUDY).

    Parameters
    ----------
    local_node : Union[DicomNode, dict]
        The local DICOM node initiating the C-MOVE requests.
    called_node : Union[DicomNode, dict]
        The called DICOM node that contains the the DICOM
        resources.
    resources : List[str]
        The list of DICOM resources to move.
    query_level : QueryLevel
        If the resources are study UID values, this should be
        set to STUDY. If the resources are patient ID values,
        this should be set to PATIENT.
    dest_node : Union[DicomNode, dict]
        The DICOM node to move the requested resources to. If
        unset, this will be equal to the local_node.
    directory : str
        Specify the directory in which to store the DICOM files.
        The default is the current directory.
    sort_by : StorageKey
        The method by which DICOM files should be stored. The
        default is PATIENT
    start_time : Union[str, time]
        If set, specify the time of the day at which C-MOVE requests
        should start. If a string, it must be in ISO format (eg:
        HH, HH:MM, HH:MM:SS). The end_time parameter must also be
        set.
    end_time : Union[str, time]
        If set, specify the time of the day at which C-MOVE requests
        should end. If a string, it must be in ISO format (eg:
        HH, HH:MM, HH:MM:SS). The start_time parameter must also be
        set.
    db_session : Session
        The database session to use if move results are to be stored
        in a database.
    callbacks : List[Callable[[Any], Any]]
        The callbacks to pass on to the storescp server.

    Yields
    ------
    Tuple[int, str]
        Yield tuples where the first element corresponds to the
        C-MOVE request status and where the second element corresponds
        to the requested UID.
    """
    if dest_node is None:
        dest_node = local_node
    if isinstance(local_node, dict):
        local_node = DicomNode(**local_node)
    if isinstance(called_node, dict):
        called_node = DicomNode(**called_node)
    if isinstance(dest_node, dict):
        dest_node = DicomNode(**dest_node)

    if not dest_node.has_port():
        raise ValueError(f"{dest_node} does not have a set port.")

    move_config = MoveConfig(
        start_time=start_time, end_time=end_time, query_level=query_level
    )

    if QueryLevel.PATIENT == move_config.query_level:
        root_model, query_lvl = PatientRootQueryRetrieveInformationModelMove, "PATIENT"
    else:
        root_model, query_lvl = StudyRootQueryRetrieveInformationModelMove, "STUDY"

    with StoreSCPServer(
        dest_node,
        data_dir=directory,
        sort_by=sort_by,
        db_session=db_session,
        callbacks=callbacks,
    ):
        ae = AE(ae_title=local_node.aetitle)
        ae.add_requested_context(root_model)

        for uid in resources:
            while not move_config.can_query():
                sleep(20)

            ds = Dataset()
            ds.QueryRetrieveLevel = query_lvl
            if query_lvl == "PATIENT":
                ds.PatientID = uid
            else:
                ds.StudyInstanceUID = uid

            assoc = None
            try:
                assoc = ae.associate(
                    called_node.ip, called_node.port, ae_title=called_node.aetitle
                )
                if assoc.is_established:
                    logger.info("Established association")
                    responses = assoc.send_c_move(ds, dest_node.aetitle, root_model)
                    for (status, _) in responses:
                        if status:
                            yield status, uid
                        else:
                            yield Status.STATUS_FAILURE, uid  # pylint: disable=no-member
                else:
                    logger.warning(
                        f"Failed to establish a connection with {called_node}."
                    )
                    yield Status.STATUS_FAILURE, uid  # pylint: disable=no-member
            finally:
                if assoc is not None and assoc.is_alive():
                    assoc.release()


def move_studies(
    local_node: DicomNode,
    called_node: DicomNode,
    *,
    study_uids: List[str],
    dest_node: DicomNode = None,
    directory: str = "",
    sort_by: StorageSortKey = StorageSortKey.PATIENT,
    start_time: Union[str, time] = None,
    end_time: Union[str, time] = None,
    db_session: Session = None,
) -> Generator[Tuple[int, str], None, None]:
    """Move studies requested by the local_node to the
    dest_node by querying the called_node. Studies to move
    should be represented by their StudyInstanceUID values.

    Parameters
    ----------
    local_node : DicomNode
        The local DICOM node initiating the C-MOVE requests.
    called_node : DicomNode
        The called DICOM node that contains the the DICOM
        resources.
    study_uids : List[str]
        The list of StudyInstanceUID values to move.
    dest_node : DicomNode
        The DICOM node to move the requested resources to. If
        unset, this will be equal to the local_node.
    directory : str
        Specify the directory in which to store the DICOM files.
        The default is the current directory.
    sort_by : StorageKey
        The method by which DICOM files should be stored. The
        default is PATIENT.
    start_time : Union[str, time]
        If set, specify the time of the day at which C-MOVE requests
        should start. If a string, it must be in ISO format (eg:
        HH, HH:MM, HH:MM:SS). The end_time parameter must also be
        set.
    end_time : Union[str, time]
        If set, specify the time of the day at which C-MOVE requests
        should end. If a string, it must be in ISO format (eg:
        HH, HH:MM, HH:MM:SS). The start_time parameter must also be
        set.
    db_session : Session
        The database session to use if move results are to be stored
        in a database.

    Yields
    ------
    Tuple[int, str]
        Yield tuples where the first element corresponds to the
        C-MOVE request status and where the second element corresponds
        to the requested UID.
    """
    yield from move(
        local_node,
        called_node,
        resources=study_uids,
        query_level=QueryLevel.STUDY,
        dest_node=dest_node,
        directory=directory,
        sort_by=sort_by,
        start_time=start_time,
        end_time=end_time,
        db_session=db_session,
    )


def move_patients(
    local_node: DicomNode,
    called_node: DicomNode,
    *,
    patient_ids: List[str],
    dest_node: DicomNode = None,
    directory: str = "",
    sort_by: StorageSortKey = StorageSortKey.PATIENT,
    start_time: Union[str, time] = None,
    end_time: Union[str, time] = None,
    db_session: Session = None,
) -> Generator[Tuple[int, str], None, None]:
    """Move patients requested by the local_node to the
    dest_node by querying the called_node. Studies to move
    should be represented by their StudyInstanceUID values.

    Parameters
    ----------
    local_node : DicomNode
        The local DICOM node initiating the C-MOVE requests.
    called_node : DicomNode
        The called DICOM node that contains the the DICOM
        resources.
    patient_ids : List[str]
        The list of PatientID values to move.
    dest_node : DicomNode
        The DICOM node to move the requested resources to. If
        unset, this will be equal to the local_node.
    directory : str
        Specify the directory in which to store the DICOM files.
        The default is the current directory.
    sort_by : StorageKey
        The method by which DICOM files should be stored. The
        default is PATIENT.
    start_time : Union[str, time]
        If set, specify the time of the day at which C-MOVE requests
        should start. If a string, it must be in ISO format (eg:
        HH, HH:MM, HH:MM:SS). The end_time parameter must also be
        set.
    end_time : Union[str, time]
        If set, specify the time of the day at which C-MOVE requests
        should end. If a string, it must be in ISO format (eg:
        HH, HH:MM, HH:MM:SS). The start_time parameter must also be
        set.
    db_session : Session
        The database session to use if move results are to be stored
        in a database.

    Yields
    ------
    Tuple[int, str]
        Yield tuples where the first element corresponds to the
        C-MOVE request status and where the second element corresponds
        to the requested UID.
    """
    yield from move(
        local_node,
        called_node,
        resources=patient_ids,
        query_level=QueryLevel.PATIENT,
        dest_node=dest_node,
        directory=directory,
        sort_by=sort_by,
        start_time=start_time,
        end_time=end_time,
        db_session=db_session,
    )
