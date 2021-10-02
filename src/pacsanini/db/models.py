# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The models module provides classes that are used to represent DICOM data
in a SQL database.
"""
from datetime import datetime
from typing import List

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class StudyFind(Base):
    """Table corresponding to the studies that were found using
    C-FIND operations.
    """

    __tablename__ = "studies_find"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String)
    patient_id = Column(String)
    study_uid = Column(String, index=True, unique=True)
    study_date = Column(DateTime)
    accession_number = Column(String)
    retrieved_on = Column(DateTime, default=None)
    found_on = Column(DateTime, default=datetime.utcnow)

    study: "Study" = relationship("Study", back_populates="study_find")

    def __repr__(self):
        study_date = self.study_date.strftime("%Y%m%d")
        return f"<StudyFind: pid={self.patient_id}, pn={self.patient_name}, sd={study_date}>"

    @classmethod
    def cfind_fields(cls) -> List[str]:
        """Returns the fields names that can be used for C-FIND queries."""
        return [
            "PatientName",
            "PatientID",
            "StudyInstanceUID",
            "StudyDate",
            "AccessionNumber",
        ]


class Patient(Base):
    """Table corresponding to patient-level data found in
    DICOM files.
    """

    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)
    patient_id = Column(String, unique=True)
    patient_name = Column(String)
    patient_birth_date = Column(DateTime)
    institution = Column(String)

    def __repr__(self) -> str:
        return f"<Patient: {self.patient_id}>"


class Study(Base):
    """Table corresponding to study-level data found in
    DICOM files.
    """

    __tablename__ = "studies"

    id = Column(Integer, primary_key=True)
    study_find_id = Column(Integer, ForeignKey("studies_find.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    study_uid = Column(String, unique=True)
    study_date = Column(DateTime)
    patient_age = Column(Integer, default=-1)
    accession_number = Column(String)

    study_find: "StudyFind" = relationship("StudyFind", back_populates="study")

    def __repr__(self) -> str:
        return f"<Study: {self.study_uid}>"


class Series(Base):
    """Table corresponding to series-level data found in
    DICOM files.
    """

    __tablename__ = "series"

    id = Column(Integer, primary_key=True)
    study_id = Column(Integer, ForeignKey("studies.id"))
    series_uid = Column(String, unique=True)
    modality = Column(String)

    def __repr__(self) -> str:
        return f"<Series: {self.series_uid}"


class Image(Base):
    """Table corresponding to the studies that were queried and
    retrieved from the PACS.
    """

    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    series_id = Column(Integer, ForeignKey("series.id"))
    institution = Column(String)
    patient_id = Column(String, index=True)
    patient_name = Column(String)
    study_uid = Column(String, index=True)
    study_date = Column(DateTime)
    series_uid = Column(String)
    modality = Column(String)
    sop_class_uid = Column(String)
    image_uid = Column(String, unique=True)
    acquisition_time = Column(Float, default=-1)
    manufacturer = Column(String)
    manufacturer_model_name = Column(String)
    meta = Column(JSON, nullable=True)
    filepath = Column(String, nullable=True)

    def __repr__(self):
        return f"<Image: {self.image_uid}>"
