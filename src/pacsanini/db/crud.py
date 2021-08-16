# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The crud module provides methods and classes that can be used to insert
single items (studies found from C-FIND requests or DICOM metadata) into a
given database.
"""
from functools import lru_cache

from loguru import logger
from pydicom import Dataset
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from pacsanini import convert
from pacsanini.db.models import Base, Images, StudyFind


TAG_MAPPING = {
    "patient_name": "PatientName",
    "patient_id": "PatientID",
    "study_uid": "StudyInstanceUID",
    "study_date": "StudyDate",
    "accession_number": "AccessionNumber",
    "series_uid": "SeriesInstanceUID",
    "modality": "Modality",
    "sop_class_uid": "SOPClassUID",
    "image_uid": "SOPInstanceUID",
    "manufacturer": "Manufacturer",
}


def add_found_study(dcm: Dataset, session: Session) -> None:
    """Add study metadata to the database after a successfull C-FIND
    operation.

    Parameters
    ----------
    dcm : Dataset
        The retrieved Dataset instance resulting from a C-FIND operation.
    session : Session
        The database session.
    """
    fields = [
        ("PatientName", "patient_name"),
        ("PatientID", "patient_id"),
        ("StudyInstanceUID", "study_uid"),
        ("StudyDate", "study_date"),
        ("AccessionNumber", "accession_number"),
    ]

    db_study = StudyFind()
    for (attr, alias) in fields:
        if attr not in dcm:
            value = None
        else:
            elem = dcm[attr]
            value = elem.value
            if elem.VR == "PN":
                value = str(value)
            elif attr == "StudyDate":
                value = convert.str2datetime(value)  # type: ignore

        setattr(db_study, alias, value)

    session.add(db_study)
    session.commit()


def add_image(
    dcm: Dataset, session: Session, institution_name: str = None, filepath: str = None
):
    """Add image metadata to the database. If the image's StudyInstanceUID's value
    can be found in the `studies_find` table, the image will be linked to it by
    populating the study_find_id field.

    Parameters
    ----------
    dcm : Dataset
        The DICOM instance to add to the database.
    session : Session
        The database session to use.
    institution_name : str
        The name of the institution to associate the image with.
    filepath : str
        If set, fill in the filepath value for the new DICOM record.
    """
    result = (
        session.query(Images).filter(Images.image_uid == dcm.SOPInstanceUID).first()
    )
    if result:
        logger.warning(
            f"{dcm.SOPInstanceUID} already exists in the database. Skipping new insert."
        )
        return

    db_image = Images()

    for column in Images.__table__.columns:
        col_name = column.name
        if col_name not in TAG_MAPPING:
            continue
        alias = col_name
        attr = TAG_MAPPING[alias]

        if attr not in dcm:
            value = None
        else:
            elem = dcm[attr]
            if elem.VR == "PN":
                value = str(elem.value)
            elif attr == "StudyDate":
                value = convert.str2datetime(elem.value)  # type: ignore
            else:
                value = elem.value
        setattr(db_image, alias, value)

    db_image.meta = convert.dcm2dict(dcm, include_pixels=False)
    db_image.institution_name = institution_name

    result = (
        session.query(StudyFind)
        .filter(StudyFind.study_uid == dcm.StudyInstanceUID)
        .first()
    )
    if result:
        db_image.study_find_id = result.id
    if filepath:
        db_image.filepath = filepath

    session.add(db_image)
    session.commit()


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
            Base.metadata.create_all(bind=self.engine, checkfirst=True)
        Session_ = sessionmaker(bind=self.engine)
        self.session = Session_()
        return self.session

    def close(self):
        """Close the instance's current session and engine if they are still open."""
        if self.session is not None:
            self.session.close()
        if self.engine is not None:
            self.engine.dispose()
