# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
# pylint: disable=redefined-outer-name
"""Expose high-level test configuration fixtures to be used by
multiple test modules.
"""
import os
import socket

from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

import pydicom
import pytest
import requests
import yaml

from pytest_docker.plugin import Services

from pacsanini.config import PacsaniniConfig
from pacsanini.net.c_store import send_dicom


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


@pytest.fixture(scope="session")
def orthanc_client_modality() -> Dict[str, Any]:
    sock = None
    host = "localhost"
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        host = sock.getsockname()[0]
    finally:
        if sock is not None:
            sock.close()
    return {"AET": "pacsanini", "Host": host, "Port": 11112}


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    """Specify the non-default location of the docker-compose file."""
    return os.path.join(
        str(pytestconfig.rootdir), "tests", "docker", "docker-compose.yaml"
    )


@pytest.fixture(scope="session")
def orthanc_node(
    docker_ip: str,
    docker_services: Services,
    orthanc_client_modality: Dict[str, Any],
    data_dir: str,
    dicom: pydicom.FileDataset,
) -> Tuple[str, str, int]:
    """Return the Orthanc instance's address and ensure that it contains the
    data.
    """
    dicom_port = docker_services.port_for("orthanc", 4242)
    http_port = docker_services.port_for("orthanc", 8042)

    orthanc_user = "orthanc123"
    orthanc_pass = "orthanc123"
    auth_creds = (orthanc_user, orthanc_pass)

    url = f"http://{docker_ip}:{http_port}/modalities/{orthanc_client_modality['AET']}"
    res = requests.put(url, json=orthanc_client_modality, auth=auth_creds)
    assert res.status_code == 200

    study_dir = os.path.join(data_dir, "dicom-files", dicom.StudyInstanceUID)
    results = send_dicom(
        study_dir,
        src_node={"aetitle": "pacsanini"},
        dest_node={"aetitle": "TPXORTHANC", "ip": docker_ip, "port": dicom_port},
    )
    for res in results:
        assert res.Status == 0  # type: ignore

    return "TPXORTHANC", docker_ip, dicom_port


@pytest.fixture(scope="session")
def pacsanini_orthanc_config(
    tmpdir_factory,
    dicom: pydicom.FileDataset,
    orthanc_node: Tuple[str, str, int],
    orthanc_client_modality: Dict[str, Any],
):
    """Generate a temporary configuration file with pre-filled settings for
    future tests that require interacting with Orthanc.
    """
    tmpdir = tmpdir_factory.mktemp("data")

    config_path = os.path.join(str(tmpdir), "pacsanini.yaml")
    data_dir = os.path.join(str(tmpdir), "dcmdir")
    sqlite_db = os.path.join(f"sqlite:///{str(tmpdir)}", "resources.db")

    study_date = datetime.strptime(dicom.StudyDate, "%Y%m%d")
    before = (study_date - timedelta(days=1)).strftime("%Y%m%d")
    after = (study_date + timedelta(days=1)).strftime("%Y%m%d")

    config = PacsaniniConfig(
        move={"query_level": "STUDY"},
        net={
            "local_node": {
                "aetitle": orthanc_client_modality["AET"],
                "ip": orthanc_client_modality["Host"],
                "port": orthanc_client_modality["Port"],
            },
            "dest_node": {
                "aetitle": orthanc_client_modality["AET"],
                "ip": orthanc_client_modality["Host"],
                "port": orthanc_client_modality["Port"],
            },
            "called_node": {
                "aetitle": orthanc_node[0],
                "ip": orthanc_node[1],
                "port": orthanc_node[2],
            },
        },
        find={"query_level": "STUDY", "start_date": before, "end_date": after},
        storage={"resources": sqlite_db, "directory": data_dir},
    )
    config_dict = config.dict()
    with open(config_path, "w") as out:
        yaml.safe_dump(config_dict, out)
    return config_path
