# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Provide fixtures for the net module testing suite."""
import os

import pytest

from pydicom import Dataset, dcmread
from pynetdicom import AE, ALL_TRANSFER_SYNTAXES, AllStoragePresentationContexts, evt
from pynetdicom.events import Event
from pynetdicom.sop_class import (  # PatientRootQueryRetrieveInformationModelGet,; StudyRootQueryRetrieveInformationModelGet,
    PatientRootQueryRetrieveInformationModelFind,
    PatientRootQueryRetrieveInformationModelMove,
    StudyRootQueryRetrieveInformationModelFind,
    StudyRootQueryRetrieveInformationModelMove,
    VerificationSOPClass,
)


@pytest.fixture
def test_dest_node() -> dict:
    """Return a DICOM node as a dict that can
    be used to test the net functionalities.
    """
    return {"aetitle": "pacsanini_testing_server", "ip": "localhost", "port": 11112}


@pytest.fixture
def test_src_node() -> dict:
    """Return a DICOM node as a dict that can
    be used to initiate network queries.
    """
    return {"aetitle": "pacsanini_testing", "ip": 11114}


@pytest.fixture
def test_dicom_server(test_dest_node: dict, data_dir: str):
    """Yield a mock DICOM server that can be used for testing."""
    dicom_dir = os.path.join(data_dir, "dicom-files")

    ae = AE(ae_title=test_dest_node["aetitle"])
    ae.add_supported_context(VerificationSOPClass, ALL_TRANSFER_SYNTAXES)
    for context in AllStoragePresentationContexts:
        ae.add_supported_context(
            context.abstract_syntax,
            ALL_TRANSFER_SYNTAXES,
            scp_role=True,
            scu_role=False,
        )

    ae.add_supported_context(PatientRootQueryRetrieveInformationModelFind)
    ae.add_supported_context(PatientRootQueryRetrieveInformationModelMove)
    ae.add_supported_context(StudyRootQueryRetrieveInformationModelFind)
    ae.add_supported_context(StudyRootQueryRetrieveInformationModelMove)

    def handle_cfind(event: Event, data_dir: str):
        model = event.request.AffectedSOPClassUID
        if model not in ["PATIENT", "STUDY"]:
            yield 0xC320, None
            return

        results = []
        for root, _, files in os.walk(data_dir):
            for name in files:
                path = os.path.join(root, name)
                dcm = dcmread(path, stop_before_pixels=True)

                ds = Dataset()
                is_ok = False
                for key, value in event.identifier.items():
                    tag_name = value.name
                    if value.value:
                        search_val = value.value
                        if tag_name == "StudyDate" and "-" in search_val:
                            lower_date, upper_date = (
                                search_val.split("-")[0],
                                search_val.split("-")[1],
                            )
                            is_ok = lower_date <= search_val <= upper_date
                        else:
                            is_ok = getattr(dcm, tag_name, None) == search_val
                    setattr(ds, tag_name, getattr(dcm, tag_name, None))

                if is_ok:
                    results.append(ds)

        for res in results:
            yield 0xFF00, res

    def handle_cmove(event: Event, data_dir: str):
        yield "localhost", "11114", {"contexts": []}
        yield 0
        yield 0xFE00, None
        return

    handlers = [
        (evt.EVT_C_FIND, handle_cfind, [data_dir]),
        (evt.EVT_C_MOVE, handle_cmove, [data_dir]),
    ]
    server = None
    try:
        server = ae.start_server(
            ("", test_dest_node["port"]), evt_handlers=handlers, block=False
        )
        yield ae
    finally:
        if server is not None:
            server.shutdown()
