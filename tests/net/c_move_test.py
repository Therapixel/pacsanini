# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that the C-MOVE operations function correctly."""
import os

import pytest

from pydicom import dcmread
from pydicom.dataset import Dataset
from pynetdicom import AE, StoragePresentationContexts, evt
from pynetdicom.events import Event
from pynetdicom.sop_class import (  # pylint: disable=no-name-in-module
    PatientRootQueryRetrieveInformationModelMove,
    StudyRootQueryRetrieveInformationModelMove,
)
from pynetdicom.transport import ThreadedAssociationServer

from pacsanini.net import c_move


@pytest.fixture(scope="module")
def dcm(dicom_path: str):
    """Return a test DICOM file."""
    return dcmread(dicom_path, stop_before_pixels=True)


@pytest.mark.net
@pytest.mark.skip(msg="Not ready")
class TestCMove:
    """Test that emitting C-MOVE requests functions correctly."""

    def setup(self):  # pylint: disable=attribute-defined-outside-init
        """Setup the server."""
        self.scp: ThreadedAssociationServer = None
        self.testing_node = {"aetitle": "pacsanini_testing", "ip": "", "port": 11114}

    def teardown(self):
        """Ensure that the server is shutdown."""
        if self.scp is not None:
            self.scp.shutdown()
            self.scp = None

    def test_patient_move(self, dcm: Dataset, tmpdir: os.PathLike):
        """Test that moving patients functions correctly."""

        def handle_cmove_request(event: Event):
            if event.dataset is None:
                status = Dataset()
                status.Status = 0xFF01
                yield status, dcm
                return

            ds = event.dataset
            status = Dataset()

            assert "QueryRetrieveLevel" in ds

            yield ("localhost", self.testing_node["port"])

            if ds.QueryRetrieveLevel == "PATIENT":
                assert ds.PatientID == dcm.PatientID
            if ds.QueryRetrieveLevel == "STUDY":
                assert ds.StudyInstanceUID == dcm.StudyInstanceUID

            yield 1
            yield 0xFF00, dcm

        handlers = [(evt.EVT_C_MOVE, handle_cmove_request)]
        ae = AE()
        ae.requested_contexts = StoragePresentationContexts
        ae.add_supported_context(PatientRootQueryRetrieveInformationModelMove)
        ae.add_supported_context(StudyRootQueryRetrieveInformationModelMove)

        self.scp = ae.start_server(
            ("", 11114),
            ae_title=b"pacsanini_testing",
            evt_handlers=handlers,
            block=False,
        )

        results = c_move.move_studies(
            {"aetitle": "pacsanini_testing", "port": 11112},
            {"aetitle": "pacsanini_testing", "ip": "localhost", "port": 11114},
            study_uids=[dcm.StudyInstanceUID],
            directory=str(tmpdir),
        )
        next(results)

        expected_path = os.path.join(
            str(tmpdir),
            dcm.PatientID,
            dcm.StudyInstanceUID,
            dcm.SeriesInstanceUID,
            f"{dcm.SOPInstanceUID}.dcm",
        )
        assert os.path.exists(expected_path)
        result_dcm = dcmread(expected_path)
        assert isinstance(result_dcm)
