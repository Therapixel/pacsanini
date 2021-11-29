# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The crud module provides methods and classes that can be used to insert
single items (studies found from C-FIND requests or DICOM metadata) into a
given database.
"""
from datetime import datetime
from functools import lru_cache
from typing import List, Optional, Union

from loguru import logger
from pydicom import Dataset
from sqlalchemy import create_engine, exc
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from pacsanini.config import PacsaniniConfig, StorageConfig
from pacsanini.db.dcm2model import dcm2dbmodels, dcm2study_finding
from pacsanini.db.models import Image, Patient, Series, Study, StudyFind


def add_found_study(session: Session, dcm: Dataset) -> Optional[StudyFind]:
    """Add study metadata to the database after a successfull C-FIND
    operation.

    Parameters
    ----------
    dcm : Dataset
        The retrieved Dataset instance resulting from a C-FIND operation.
    session : Session
        The database session.
    """
    study_find = dcm2study_finding(dcm)

    try:
        session.add(study_find)
        session.commit()
    except exc.IntegrityError:
        session.rollback()
        return None
    else:
        return study_find


def add_image(
    session: Session,
    dcm: Union[str, Dataset],
    institution: str = None,
    filepath: str = None,
) -> Optional[Image]:
    """Insert an image to the database. If the image belongs to a new patient, study, or
    series, the relevant tables will also be updated. If the image already exists in the
    database (based on the SOPInstanceUID), the transaction will be rolled back.

    Parameters
    ----------
    session : Session
        The database session to use for inserting the DICOM image into the database.
    dcm : Union[str, Dataset]
        The DICOM image to add to the database.
    institution : str
        The institution that the DICOM image belongs to. The default is None.
    filepath : str
        The DICOM image's filepath. The default is None.

    Returns
    -------
    Image
        The inserted Image object. If the insert was unsuccessfull, None
        is returned.
    """
    pat, study, series, image = dcm2dbmodels(
        dcm, institution=institution, filepath=filepath
    )

    try:
        session.add(pat)
        session.flush()
        pat_dbid = pat.id
    except exc.IntegrityError:
        session.rollback()
        pat_dbid = (
            session.query(Patient.id)
            .filter(Patient.patient_id == pat.patient_id)
            .first()[0]
        )

    study.patient_id = pat_dbid
    try:
        session.add(study)
        session.flush()
        study_dbid = study.id
    except exc.IntegrityError:
        session.rollback()
        study_dbid = (
            session.query(Study.id)
            .filter(Study.study_uid == study.study_uid)
            .first()[0]
        )

    series.study_id = study_dbid
    try:
        session.add(series)
        session.flush()
        series_dbid = series.id
    except exc.IntegrityError:
        session.rollback()
        series_dbid = (
            session.query(Series.id)
            .filter(Series.series_uid == series.series_uid)
            .first()[0]
        )

    image.series_id = series_dbid
    try:
        session.add(image)
        session.commit()
    except exc.IntegrityError:
        logger.warning("{image} already exists in the database. Rolling back commit...")
        session.rollback()
        return None
    else:
        return image


def update_retrieved_study(session: Session, study_uid: str) -> Optional[StudyFind]:
    """Update a found study by setting its retrieved_on value to the current
    date. If the relevant study was already retrieved, it will not be updated
    but the StudyFind instance will be returned. If the found study does not
    exist, None is returned.

    Parameters
    ----------
    session : Session
        The database session to use.
    study_uid : str
        The study instance uid to mark as retrieved.

    Returns
    -------
    Optional[StudyFind]
        The StudyFind instance if it was found or updated. None otherwise.
    """
    found_study: StudyFind = (
        session.query(StudyFind).filter(StudyFind.study_uid == study_uid).first()
    )
    if found_study is None:
        return None

    if found_study.retrieved_on is None:
        found_study.retrieved_on = datetime.utcnow()
        session.add(found_study)
        session.commit()
    return found_study


def get_studies_to_move(session: Session) -> List[StudyFind]:
    """Get a list of StudyFind instances that haven't been retrieved
    according to their `retrieved_on` key.

    Parameters
    ----------
    session : Session
        The database session to use.

    Returns
    -------
    List[StudyFind]
        A list of StudyFind resources that should be moved.
    """
    query = session.query(StudyFind).filter(StudyFind.retrieved_on == None)
    return query.all()


def get_study_uids_to_move(session: Session) -> List[str]:
    """Get a list of StudyInstanceUID values to retrieve.

    Parameters
    ----------
    session : Session
        The database session to use.

    Returns
    -------
    List[str]
        A list of StudyInstanceUID resources that should be moved.
    """
    return [study_find.study_uid for study_find in get_studies_to_move(session)]


class DBWrapper:
    """A wrapper class for the database connections. The purpose of this is
    to be able to open database connections lazily inside a thread that may
    not be the application's main thread. It is recommended to use instances
    of this class inside a context manager.

    Attributes
    ----------
    conn_uri : str
        The database connection URI.
    create_tables : bool
        Whether to create tables when the connection is first established.
        The default is False.
    debug : bool
        If True, echo SQL statements to the standard output. The default
        is False.
    """

    def __init__(self, conn_uri: str, create_tables: bool = False, debug: bool = False):
        self.conn_uri = conn_uri
        self.create_tables = create_tables
        self.debug = debug
        self.engine: Engine = None
        self.session: Session = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @lru_cache(maxsize=1)
    def conn(self) -> Session:
        """Obtain a session instance"""
        self.engine = create_engine(self.conn_uri)
        if self.create_tables:
            config = PacsaniniConfig(
                storage=StorageConfig(resources=self.conn_uri, directory="./")
            )
            from pacsanini.db.utils import (  # pylint: disable=import-outside-toplevel
                initialize_database,
            )

            initialize_database(config)
        DBSession = sessionmaker(bind=self.engine)
        self.session = DBSession()
        return self.session

    def close(self):
        """Close the instance's current session and engine if they are still open."""
        if self.session is not None:
            self.session.close()
        if self.engine is not None:
            self.engine.dispose()
