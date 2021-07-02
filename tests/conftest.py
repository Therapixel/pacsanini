# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
# pylint: disable=redefined-outer-name
"""Expose high-level test configuration fixtures to be used by
multiple test modules.
"""
import os

import pydicom
import pytest


@pytest.fixture(scope="session")
def data_dir() -> str:
    """Return the test data directory for the tests."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(current_dir, "data")
    return test_dir


@pytest.fixture(scope="session")
def dicom_path(data_dir: str) -> str:
    """Return a path to a reference DICOM file."""
    return os.path.join(
        data_dir,
        "dicom-files",
        "2.25.251902960533573151000097783431958561263",
        "2.25.171393445333099000331008511307816546527",
        "2.25.98665557379884205730193271628654420727.dcm",
    )


@pytest.fixture(scope="session")
def dicom(dicom_path: str) -> pydicom.FileDataset:
    """Return a pre-loaded DICOM file."""
    return pydicom.dcmread(dicom_path)


@pytest.fixture(scope="session")
def test_config_path(data_dir: str) -> str:
    """Return the path of the test configuration file."""
    return os.path.join(data_dir, "test_conf.yaml")
