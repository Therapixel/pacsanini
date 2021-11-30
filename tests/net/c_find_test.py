# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test the C-Find message are correctly sent
and can provide useful results.
"""
import os

from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator

import pytest

from pynetdicom import debug_logger
from pytest import CaptureFixture

from pacsanini.config import PacsaniniConfig
from pacsanini.models import QueryLevel
from pacsanini.net import c_find


def validate_results(sys_capture, results, query_level, query_fields):
    """Validate that c-find results are ok."""
    assert isinstance(results, Generator)

    results_list = list(results)
    out = sys_capture.readouterr()
    assert query_level in out.err

    for result in results_list:
        for field in query_fields:
            assert hasattr(result, field)


@pytest.mark.net
def test_find_single_date(capsys: CaptureFixture, pacsanini_orthanc_config: str):
    """Test that the find method functions correctly.
    Check that the query level is correctly set to the patient
    level by looking at the output logs.
    """
    config = PacsaniniConfig.from_yaml(pacsanini_orthanc_config)

    query_fields = ["SOPClassUID", "PatientBirthDate"]
    debug_logger()

    patient_level_results = c_find.patient_find(
        config.net.local_node.dict(),
        config.net.called_node.dict(),
        dicom_fields=query_fields,
        start_date=datetime(2016, 6, 22),
    )

    validate_results(
        capsys,
        patient_level_results,
        "Patient Root Query/Retrieve Information Model - FIND",
        query_fields,
    )

    study_level_results = c_find.study_find(
        config.net.local_node,
        config.net.called_node,
        dicom_fields=query_fields,
        start_date=datetime(2010, 12, 1),
    )
    validate_results(
        capsys,
        study_level_results,
        "Study Root Query/Retrieve Information Model - FIND",
        query_fields,
    )


@pytest.mark.net
def test_find_multiple_dates(
    capsys: CaptureFixture, pacsanini_orthanc_config: str, tmpdir: Path
):
    """Test that the find method functions correctly.
    Check that the query level is correctly set to the patient
    level by looking at the output logs.
    """
    config = PacsaniniConfig.from_yaml(pacsanini_orthanc_config)

    query_fields = ["Modality", "PatientBirthDate"]
    debug_logger()

    patient_out_path = os.path.join(tmpdir, "patient_results.csv")
    c_find.patient_find2csv(
        config.net.local_node,
        config.net.called_node,
        patient_out_path,
        dicom_fields=query_fields,
        start_date=datetime.now() - timedelta(days=23),
        end_date=datetime.now(),
    )
    assert os.path.exists(patient_out_path)
    out = capsys.readouterr()
    assert "Patient Root Query/Retrieve Information Model - FIND" in out.err

    study_out_path = os.path.join(tmpdir, "study_results.csv")
    c_find.study_find2csv(
        config.net.local_node,
        config.net.called_node,
        study_out_path,
        dicom_fields=query_fields,
        start_date=datetime.now() - timedelta(days=23),
        end_date=datetime.now(),
    )
    assert os.path.exists(study_out_path)
    out = capsys.readouterr()
    assert "Study Root Query/Retrieve Information Model - FIND" in out.err


@pytest.mark.net
def test_find_invalid_parameters(pacsanini_orthanc_config: str):
    """Test that with invalid parameters, the find functionality
    responds with expected errors.
    """
    config = PacsaniniConfig.from_yaml(pacsanini_orthanc_config)
    invalid_dates = c_find.find(
        config.net.local_node,
        config.net.called_node,
        query_level=QueryLevel.PATIENT,
        dicom_fields=["PatientID"],
        start_date=datetime.now(),
        end_date=datetime.now() - timedelta(days=1),
    )
    with pytest.raises(ValueError):
        list(invalid_dates)

    called_node = config.net.called_node.dict()
    called_node.pop("ip", None)
    invalid_dest_node = c_find.find(
        config.net.local_node,
        called_node,
        query_level=QueryLevel.PATIENT,
        dicom_fields=["PatientID"],
        start_date=datetime.now(),
    )
    with pytest.raises(ValueError):
        list(invalid_dest_node)
