# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The models module provides classes that are used to represent DICOM data
in a SQL database.
"""
from datetime import datetime
from typing import List

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
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
    retrieved = Column(Boolean, default=False)
    found_on = Column(DateTime, default=datetime.utcnow)

    images: "Images" = relationship("Images", back_populates="study_find")

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


class Images(Base):
    """Table corresponding to the studies that were queried and
    retrieved from the PACS.
    """

    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    study_find_id = Column(Integer, ForeignKey("studies_find.id"), nullable=True)
    institution_name = Column(String)
    patient_id = Column(String)
    patient_name = Column(String)
    study_uid = Column(String)
    study_date = Column(DateTime)
    series_uid = Column(String)
    modality = Column(String)
    sop_class_uid = Column(String)
    image_uid = Column(String, index=True)
    manufacturer = Column(String)
    meta = Column(JSON, nullable=True)
    filepath = Column(String, nullable=True)

    study_find: "StudyFind" = relationship("StudyFind", back_populates="images")

    def __repr__(self):
        study_date = (
            self.study_date.strftime("%Y%m%d") if self.study_date is not None else None
        )
        return f"<Image: pid={self.patient_id}, sd={study_date}, iuid={self.image_uid}>"
