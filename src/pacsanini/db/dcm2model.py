# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The dcm2model module provides methods that can be used to convert pydicom.Dataset
instances to sqlalchemy instances.
"""
from typing import Tuple, Union

from pydicom import Dataset, dcmread

from pacsanini.convert import agestr2years, dcm2dict, str2datetime
from pacsanini.db.models import Image, Patient, Series, Study, StudyFind
from pacsanini.parse import DicomTagGroup


def dcm2patient(dcm: Dataset, institution: str = None) -> Patient:
    """Convert a DICOM file to a Patient instance that can be inserted
    in the database.

    Parameters
    ----------
    dcm : Dataset
        The DICOM data to convert to a Patient instance.
    institution : str
        If set, add a specified institution name to the Patient
        model. The default is None.

    Returns
    -------
    Patient
        The Patient model.
    """
    tag_grp = DicomTagGroup(
        tags=[
            {"tag_name": "PatientID", "tag_alias": "patient_id"},
            {"tag_name": "PatientName", "tag_alias": "patient_name", "callback": str},
            {
                "tag_name": "PatientBirthDate",
                "tag_alias": "patient_birth_date",
                "callback": str2datetime,
            },
        ]
    )
    data = tag_grp.parse_dicom(dcm)
    data["institution"] = institution
    return Patient(**data)


def dcm2study(dcm: Dataset) -> Study:
    """Convert a DICOM file to a Study instance that can be inserted
    in the database.

    Parameters
    ----------
    dcm : Dataset
        The DICOM data to convert to a Study instance.

    Returns
    -------
    Study
        The Study model.
    """
    tag_grp = DicomTagGroup(
        tags=[
            {"tag_name": "StudyInstanceUID", "tag_alias": "study_uid"},
            {
                "tag_name": "StudyDate",
                "tag_alias": "study_date",
                "callback": str2datetime,
            },
            {
                "tag_name": "PatientAge",
                "tag_alias": "patient_age",
                "callback": agestr2years,
                "default": -1,
            },
            {"tag_name": "AccessionNumber", "tag_alias": "accession_number"},
        ]
    )
    data = tag_grp.parse_dicom(dcm)
    return Study(**data)


def dcm2study_finding(dcm: Dataset) -> StudyFind:
    """Convert a DICOM file to a StudyFind instance that can be inserted
    in the database.

    Parameters
    ----------
    dcm : Dataset
        The DICOM data to convert to a StudyFind instance.

    Returns
    -------
    StudyFind
        The StudyFind model.
    """
    tag_grp = DicomTagGroup(
        tags=[
            {"tag_name": "PatientName", "tag_alias": "patient_name", "callback": str},
            {"tag_name": "PatientID", "tag_alias": "patient_id"},
            {"tag_name": "StudyInstanceUID", "tag_alias": "study_uid"},
            {
                "tag_name": "StudyDate",
                "tag_alias": "study_date",
                "callback": str2datetime,
            },
            {"tag_name": "AccessionNumber", "tag_alias": "accession_number"},
        ]
    )
    data = tag_grp.parse_dicom(dcm)
    return StudyFind(**data)


def dcm2series(dcm: Dataset) -> Series:
    """Convert a DICOM file to a Series instance that can be inserted
    in the database.

    Parameters
    ----------
    dcm : Dataset
        The DICOM data to convert to a Series instance.

    Returns
    -------
    Series
        The Series model.
    """
    tag_grp = DicomTagGroup(
        tags=[
            {"tag_name": "SeriesInstanceUID", "tag_alias": "series_uid"},
            {"tag_name": "Modality", "tag_alias": "modality"},
        ]
    )
    data = tag_grp.parse_dicom(dcm)
    return Series(**data)


def dcm2image(dcm: Dataset, institution: str = None, filepath: str = None) -> Image:
    """Convert a DICOM file to a Image instance that can be inserted
    in the database.

    Parameters
    ----------
    dcm : Dataset
        The DICOM data to convert to a Image instance.
    institution : str
        If set, add a specified institution name to the Image
        model. The default is None.
    filepath : str
        If set, add the DICOM's filepath to the database. The default
        is None.

    Returns
    -------
    Image
        The Image model.
    """
    tag_grp = DicomTagGroup(
        tags=[
            {"tag_name": "PatientID", "tag_alias": "patient_id"},
            {"tag_name": "StudyInstanceUID", "tag_alias": "study_uid"},
            {
                "tag_name": "StudyDate",
                "tag_alias": "study_date",
                "callback": str2datetime,
            },
            {"tag_name": "SeriesInstanceUID", "tag_alias": "series_uid"},
            {"tag_name": "Modality", "tag_alias": "modality"},
            {"tag_name": "SOPClassUID", "tag_alias": "sop_class_uid"},
            {"tag_name": "SOPInstanceUID", "tag_alias": "image_uid"},
            {"tag_name": "AcquisitionTime", "tag_alias": "acquisition_time"},
            {"tag_name": "Manufacturer", "tag_alias": "manufacturer"},
            {
                "tag_name": "ManufacturerModelName",
                "tag_alias": "manufacturer_model_name",
            },
        ]
    )
    data = tag_grp.parse_dicom(dcm)
    data["meta"] = dcm2dict(dcm, include_pixels=False)
    data["institution"] = institution
    data["filepath"] = filepath
    return Image(**data)


def dcm2dbmodels(
    dcm: Union[str, Dataset], institution: str = None, filepath: str = None
) -> Tuple[Patient, Study, Series, Image]:
    """Convert a DICOM file into the different database models that will be used
    to insert the DICOM data into the database.

    Parameters
    ----------
    dcm : Union[str, Dataset]
        The DICOM data to convert to a Patient, Study, Series, and Image instance.
    institution : str
        If set, add a specified institution name to the Patient
        model. The default is None.
    filepath : str
        If set, add the DICOM's filepath to the database. The default
        is None. If the input dcm parameter value is a string, filepath
        will be set to this.

    Returns
    -------
    Tuple[Patient, Study, Series, Image]
        A 4-tuple corresponding to the image's
    """
    if isinstance(dcm, str):
        filepath = dcm
        dcm = dcmread(dcm, stop_before_pixels=True)

    pat = dcm2patient(dcm, institution=institution)
    study = dcm2study(dcm)
    series = dcm2series(dcm)
    image = dcm2image(dcm, institution=institution, filepath=filepath)
    return pat, study, series, image
