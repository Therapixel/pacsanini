# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The views module defines the different views that are available
in the pacsanini database.
"""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy_utils import create_view

from pacsanini.db.models import Base, Image, Study


STUDY_META_VIEW_SELECT = (
    select(
        [
            Image.__table__.c.patient_id,
            Study.__table__.c.study_uid,
            Study.__table__.c.study_date,
            Study.__table__.c.patient_age,
            Image.__table__.c.manufacturer,
            func.count(Image.__table__.c.id).label("image_count"),
        ]
    )
    .join(Image.__table__, Study.__table__.c.study_uid == Image.__table__.c.study_uid)
    .group_by(Study.__table__.c.study_uid)
)

MANUFACTURER_VIEW_SELECT = select(
    [
        Image.__table__.c.manufacturer,
        func.count(Image.__table__.c.id).label("image_count"),
    ]
).group_by(Image.__table__.c.manufacturer)


class StudyMetaView(Base):
    """The study_metadata view enables querying studies based
    on high-level information such as the number of images
    in each study or the study's manufacturer.

    Attributes
    ----------
    patient_id : str
        The patient ID corresponding to the study.
    study_uid : str
        The study UID to which the metadata is associated with.
    study_date : datetime.datetime
        The study's date.
    patient_age : int
        The patient's age at the time of the study.
    manufacturer : str
        The study's imaging manufacturer name.
    image_count : int
        The number of images in the study.
    """

    patient_id: str
    study_uid: str
    study_date: datetime
    patient_age: int
    manufacturer: str
    image_count: int

    __tablename__ = "study_metadata"
    __table__ = create_view(
        name="study_metadata", selectable=STUDY_META_VIEW_SELECT, metadata=Base.metadata
    )


class ManufacturerView(Base):
    """The manufacturers view enables querying for data based on manufacturer
    groups.

    Attributes
    ----------
    manufacturer : str
        The name of the manufacturer.
    image_count : int
        The number of images associated with the manufacturer name.
    """

    manufacturer: str
    image_count: int

    __tablename__ = "manufacturers"
    __table__ = create_view(
        name="manufacturers",
        selectable=MANUFACTURER_VIEW_SELECT,
        metadata=Base.metadata,
    )

    def __repr__(self) -> str:
        return f"<{self.manufacturer}: {self.image_count} images>"

    def __str__(self) -> str:
        return self.__repr__()
