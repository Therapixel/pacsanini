# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The c_find module provides methods that can be used to query
DICOM data that is stored in another DICOM node (typically a PACS).
"""
from csv import DictWriter
from datetime import datetime, timedelta
from string import ascii_lowercase
from typing import Generator, List, Union

from pydicom import Dataset
from pynetdicom import AE
from pynetdicom.sop_class import (  # pylint: disable=no-name-in-module
    PatientRootQueryRetrieveInformationModelFind,
    StudyRootQueryRetrieveInformationModelFind,
)

from pacsanini.db import DBWrapper, StudyFind, add_found_study
from pacsanini.models import DicomNode, QueryLevel


_SEARCH_FIELDS = ["Modality", "PatientName", "StudyDate"]


def find(
    local_node: Union[DicomNode, dict],
    called_node: Union[DicomNode, dict],
    *,
    query_level: Union[QueryLevel, str],
    dicom_fields: List[str],
    start_date: datetime,
    end_date: datetime = None,
    modality: str = "",
) -> Generator[Dataset, None, None]:
    """Find DICOM resources from the destination DICOM node using
    the specified DICOM criteria.

    The dicom_fields parameter are used to ask the destination
    DICOM node for additional information regarding results. If
    the destination node does not return those values, default
    values of None will be returned.

    Parameters
    ----------
    local_node : Union[DicomNode, dict]
        The source/calling DICOM node that seeks to retrieve information
        from the destination node.
    called_node : Union[DicomNode, dict]
        The destination/target node from which information is queried
        from.
    query_level : Union[QueryLevel, str]
        The query level to use when asking for data to retrieve. This
        can be "PATIENT" or "STUDY". According to this level, the values
        returned for the dicom_fields you request may change.
    dicom_fields : List[str]
        A list of DICOM tags to get information from when the destination
        node returns results.
    start_date : datetime
        The date for which the query should be made.
    end_date : datetime
        If set, queries will range from the start_date to the end_date.
        The end_date parameter must therefore be greater or equal to the
        start_date parameter.
    modality : str
        If set, specify the DICOM modality to get results for.

    Yields
    ------
    Dataset
        Each result returned by the query made to the called_node
        is yielded as a Dataset instance.

    Raises
    ------
    ValueError
        A ValueError is raised if the called_node parameter does not
        have set IP and port values or if the end_date parameter is
        set and is smaller than the start_date parameter.
    """
    if isinstance(local_node, dict):
        local_node = DicomNode(**local_node)
    if isinstance(called_node, dict):
        called_node = DicomNode(**called_node)

    if isinstance(query_level, str):
        query_level = QueryLevel(query_level)
    if query_level is QueryLevel.PATIENT:
        query_root = PatientRootQueryRetrieveInformationModelFind
    else:
        query_root = StudyRootQueryRetrieveInformationModelFind

    if not called_node.has_net_info:
        raise ValueError(f"{called_node} does not have a network address.")

    if end_date is None:
        end_date = start_date
    if end_date < start_date:
        err_msg = (
            f"The start date {start_date} cannot be greater"
            f" than the end date {end_date}"
        )
        raise ValueError(err_msg)

    ae = AE(ae_title=local_node.aetitle)
    ae.add_requested_context(query_root)

    current_date = start_date
    date_increment = timedelta(days=15)

    while current_date <= end_date:
        if (current_date + date_increment) >= end_date:
            upper_date = end_date
        else:
            upper_date = current_date + date_increment

        if current_date == end_date:
            date_str = current_date.strftime("%Y%m%d")
            requested_date = f"{date_str}"
        else:
            requested_date = (
                f"{current_date.strftime('%Y%m%d')}-{upper_date.strftime('%Y%m%d')}"
            )

        for char in ascii_lowercase:
            ds = Dataset()
            ds.Modality = modality if modality else ""
            ds.PatientName = f"{char}*"
            ds.QueryRetrieveLevel = query_level.value
            ds.StudyDate = requested_date
            for field in dicom_fields:
                if field not in _SEARCH_FIELDS:
                    setattr(ds, field, "")

            assoc = ae.associate(called_node.ip, called_node.port)
            try:
                if assoc.is_established:
                    responses = assoc.send_c_find(ds, query_root)
                    for (status, identifier) in responses:
                        if status and identifier:
                            for field in list(dicom_fields) + _SEARCH_FIELDS:
                                if not hasattr(identifier, field):
                                    setattr(identifier, field, None)
                            yield identifier
            finally:
                if assoc.is_alive():
                    assoc.release()

        current_date += date_increment + timedelta(days=1)


def patient_find(
    local_node: Union[DicomNode, dict],
    called_node: Union[DicomNode, dict],
    *,
    dicom_fields: List[str],
    start_date: datetime,
    end_date: datetime = None,
    modality: str = "",
) -> Generator[Dataset, None, None]:
    """Find DICOM resources from the destination DICOM node using the
    specified DICOM criteria. Queries are made using the PATIENT
    query retrieve level.

    Parameters
    ----------
    local_node : Union[DicomNode, dict]
        The source/calling DICOM node that seeks to retrieve information
        from the destination node.
    called_node : Union[DicomNode, dict]
        The destination/target node from which information is queried
        from.
    dicom_fields : List[str]
        A list of DICOM tags to get information from when the destination
        node returns results.
    start_date : datetime
        The date for which the query should be made.
    end_date : datetime
        If set, queries will range from the start_date to the end_date.
        The end_date parameter must therefore be greater or equal to the
        start_date parameter.
    modality : str
        If set, specify the DICOM modality to get results for.

    Yields
    ------
    Dataset
        Each result returned by the query made to the called_node
        is yielded as a Dataset instance.

    Raises
    ------
    ValueError
        A ValueError is raised if the called_node parameter does not
        have set IP and port values or if the end_date parameter is
        set and is smaller than the start_date parameter.
    """
    results = find(
        local_node,
        called_node,
        query_level=QueryLevel.PATIENT,
        dicom_fields=dicom_fields,
        start_date=start_date,
        end_date=end_date,
        modality=modality,
    )
    for res in results:
        yield res


def study_find(
    local_node: Union[DicomNode, dict],
    called_node: Union[DicomNode, dict],
    *,
    dicom_fields: List[str],
    start_date: datetime,
    end_date: datetime = None,
    modality: str = "",
) -> Generator[Dataset, None, None]:
    """Find DICOM resources from the destination DICOM node using the
    specified DICOM criteria. Queries are made using the STUDY
    query retrieve level.

    Parameters
    ----------
    local_node : Union[DicomNode, dict]
        The source/calling DICOM node that seeks to retrieve information
        from the destination node.
    called_node : Union[DicomNode, dict]
        The destination/target node from which information is queried
        from.
    dicom_fields : List[str]
        A list of DICOM tags to get information from when the destination
        node returns results.
    start_date : datetime
        The date for which the query should be made.
    end_date : datetime
        If set, queries will range from the start_date to the end_date.
        The end_date parameter must therefore be greater or equal to the
        start_date parameter.
    modality : str
        If set, specify the DICOM modality to get results for.

    Yields
    ------
    Dataset
        Each result returned by the query made to the called_node
        is yielded as a Dataset instance.

    Raises
    ------
    ValueError
        A ValueError is raised if the called_node parameter does not
        have set IP and port values or if the end_date parameter is
        set and is smaller than the start_date parameter.
    """
    results = find(
        local_node,
        called_node,
        query_level=QueryLevel.STUDY,
        dicom_fields=dicom_fields,
        start_date=start_date,
        end_date=end_date,
        modality=modality,
    )
    for res in results:
        yield res


def patient_find2csv(
    local_node: Union[DicomNode, dict],
    called_node: Union[DicomNode, dict],
    dest: str,
    *,
    dicom_fields: List[str],
    start_date: datetime,
    end_date: datetime = None,
    modality: str = "",
):
    """Find DICOM resources from the destination DICOM node using the
    specified DICOM criteria. Queries are made using the PATIENT
    query retrieve level. Returned results will be persisted the dest
    file.

    Parameters
    ----------
    local_node : Union[DicomNode, dict]
        The source/calling DICOM node that seeks to retrieve information
        from the destination node.
    called_node : Union[DicomNode, dict]
        The destination/target node from which information is queried
        from.
    dest : str
        The output path to write results to.
    dicom_fields : List[str]
        A list of DICOM tags to get information from when the destination
        node returns results.
    start_date : datetime
        The date for which the query should be made.
    end_date : datetime
        If set, queries will range from the start_date to the end_date.
        The end_date parameter must therefore be greater or equal to the
        start_date parameter.
    modality : str
        If set, specify the DICOM modality to get results for.

    Raises
    ------
    ValueError
        A ValueError is raised if the called_node parameter does not
        have set IP and port values or if the end_date parameter is
        set and is smaller than the start_date parameter.
    """
    fields = _SEARCH_FIELDS + dicom_fields
    with open(dest, "w", newline="") as out:
        writer = DictWriter(out, fieldnames=fields)
        writer.writeheader()

        results_generator = patient_find(
            local_node,
            called_node,
            dicom_fields=dicom_fields,
            start_date=start_date,
            end_date=end_date,
            modality=modality,
        )
        for result in results_generator:
            res_dict = {field: getattr(result, field) for field in fields}
            writer.writerow(res_dict)


def study_find2csv(
    local_node: Union[DicomNode, dict],
    called_node: Union[DicomNode, dict],
    dest: str,
    *,
    dicom_fields: List[str],
    start_date: datetime,
    end_date: datetime = None,
    modality: str = "",
):
    """Find DICOM resources from the destination DICOM node using the
    specified DICOM criteria. Queries are made using the STUDY
    query retrieve level. Returned results will be persisted the dest
    file.

    Parameters
    ----------
    local_node : Union[DicomNode, dict]
        The source/calling DICOM node that seeks to retrieve information
        from the destination node.
    called_node : Union[DicomNode, dict]
        The destination/target node from which information is queried
        from.
    dest : str
        The output path to write results to.
    dicom_fields : List[str]
        A list of DICOM tags to get information from when the destination
        node returns results.
    start_date : datetime
        The date for which the query should be made.
    end_date : datetime
        If set, queries will range from the start_date to the end_date.
        The end_date parameter must therefore be greater or equal to the
        start_date parameter.
    modality : str
        If set, specify the DICOM modality to get results for.

    Raises
    ------
    ValueError
        A ValueError is raised if the called_node parameter does not
        have set IP and port values or if the end_date parameter is
        set and is smaller than the start_date parameter.
    """
    fields = _SEARCH_FIELDS + dicom_fields
    with open(dest, "w", newline="") as out:
        writer = DictWriter(out, fieldnames=fields)
        writer.writeheader()

        results_generator = study_find(
            local_node,
            called_node,
            dicom_fields=dicom_fields,
            start_date=start_date,
            end_date=end_date,
            modality=modality,
        )
        for result in results_generator:
            res_dict = {field: getattr(result, field) for field in fields}
            writer.writerow(res_dict)


def patient_find2sql(
    local_node: Union[DicomNode, dict],
    called_node: Union[DicomNode, dict],
    conn_uri: str,
    *,
    start_date: datetime,
    end_date: datetime = None,
    modality: str = "",
    create_tables: bool = False,
):
    """Find DICOM resources from the destination DICOM node using the
    specified DICOM criteria. Queries are made using the PATIENT
    query retrieve level. Returned results will be persisted in the
    specified database.

    Parameters
    ----------
    local_node : Union[DicomNode, dict]
        The source/calling DICOM node that seeks to retrieve information
        from the destination node.
    called_node : Union[DicomNode, dict]
        The destination/target node from which information is queried
        from.
    conn_uri : str
        The database's connection URI.
    start_date : datetime
        The date for which the query should be made.
    end_date : datetime
        If set, queries will range from the start_date to the end_date.
        The end_date parameter must therefore be greater or equal to the
        start_date parameter.
    modality : str
        If set, specify the DICOM modality to get results for.
    create_tables : bool
        If True, create the database tables before inserting the first
        find result. The default is False.

    Raises
    ------
    ValueError
        A ValueError is raised if the called_node parameter does not
        have set IP and port values or if the end_date parameter is
        set and is smaller than the start_date parameter.
    """
    with DBWrapper(conn_uri, create_tables=create_tables) as db:
        results_generator = patient_find(
            local_node,
            called_node,
            dicom_fields=StudyFind.cfind_fields(),
            start_date=start_date,
            end_date=end_date,
            modality=modality,
        )
        for result in results_generator:
            add_found_study(db.conn(), result)


def study_find2sql(
    local_node: Union[DicomNode, dict],
    called_node: Union[DicomNode, dict],
    conn_uri: str,
    *,
    start_date: datetime,
    end_date: datetime = None,
    modality: str = "",
    create_tables: bool = False,
):
    """Find DICOM resources from the destination DICOM node using the
    specified DICOM criteria. Queries are made using the STUDY
    query retrieve level. Returned results will be persisted in the
    specified database.

    Parameters
    ----------
    local_node : Union[DicomNode, dict]
        The source/calling DICOM node that seeks to retrieve information
        from the destination node.
    called_node : Union[DicomNode, dict]
        The destination/target node from which information is queried
        from.
    conn_uri : str
        The database's connection URI.
    start_date : datetime
        The date for which the query should be made.
    end_date : datetime
        If set, queries will range from the start_date to the end_date.
        The end_date parameter must therefore be greater or equal to the
        start_date parameter.
    modality : str
        If set, specify the DICOM modality to get results for.
    create_tables : bool
        If True, create the database tables before inserting the first
        find result. The default is False.

    Raises
    ------
    ValueError
        A ValueError is raised if the called_node parameter does not
        have set IP and port values or if the end_date parameter is
        set and is smaller than the start_date parameter.
    """
    with DBWrapper(conn_uri, create_tables=create_tables) as db:
        results_generator = study_find(
            local_node,
            called_node,
            dicom_fields=StudyFind.cfind_fields(),
            start_date=start_date,
            end_date=end_date,
            modality=modality,
        )
        for result in results_generator:
            add_found_study(db.conn(), result)
