# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that the C-MOVE operations function correctly."""
import os

import pytest

from py._path.local import LocalPath
from pydicom import Dataset, dcmread

from pacsanini.config import PacsaniniConfig
from pacsanini.net import c_move


@pytest.fixture(scope="module")
def dcm(dicom_path: str):
    """Return a test DICOM file."""
    return dcmread(dicom_path, stop_before_pixels=True)


@pytest.mark.net
def test_study_move(tmpdir: LocalPath, dcm: Dataset, config: PacsaniniConfig):
    """Test that moving studies will work correctly."""
    results = c_move.move_studies(
        config.net.local_node.dict(),
        config.net.called_node.dict(),
        study_uids=[dcm.StudyInstanceUID],
        directory=str(tmpdir),
    )
    list(results)

    expected_path = os.path.join(
        str(tmpdir),
        dcm.PatientID,
        dcm.StudyInstanceUID,
        dcm.SeriesInstanceUID,
        f"{dcm.SOPInstanceUID}.dcm",
    )
    assert os.path.exists(expected_path)
    result_dcm = dcmread(expected_path)
    assert isinstance(result_dcm, Dataset)
