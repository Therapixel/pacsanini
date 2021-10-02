# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""This module tests that converting a DICOM Dataset into a pacsanini
database model functions correctly.
"""
import pytest

from pydicom import FileDataset
from pydicom.dataset import Dataset

from pacsanini.convert import datetime2str
from pacsanini.db.dcm2model import dcm2dbmodels, dcm2study_finding
from pacsanini.db.models import Image, Patient, Series, Study, StudyFind


@pytest.mark.db
def test_dcm2dbmodels(dicom_path: str, dicom: FileDataset):
    """Test that a DICOM file can correctly be converted to
    the multiple database models.
    """
    patient, study, series, image = dcm2dbmodels(dicom_path)

    assert isinstance(patient, Patient)
    assert isinstance(study, Study)
    assert isinstance(series, Series)
    assert isinstance(image, Image)

    assert patient.patient_id == dicom.PatientID

    assert study.study_uid == dicom.StudyInstanceUID

    assert series.series_uid == dicom.SeriesInstanceUID

    assert image.image_uid == dicom.SOPInstanceUID
    assert image.filepath == dicom_path


@pytest.mark.db
def test_dcm2study_finding():
    """Test that study findings are correctly converted."""
    ds = Dataset()
    ds.PatientName = "JDOE"
    ds.PatientID = "007"
    ds.StudyInstanceUID = "study1"
    ds.StudyDate = "20210102"
    ds.AccessionNumber = "accession1"

    study_finding = dcm2study_finding(ds)

    assert isinstance(study_finding, StudyFind)
    assert study_finding.patient_name == ds.PatientName
    assert study_finding.patient_id == ds.PatientID
    assert study_finding.study_uid == ds.StudyInstanceUID
    assert datetime2str(study_finding.study_date) == ds.StudyDate
    assert study_finding.accession_number == ds.AccessionNumber
