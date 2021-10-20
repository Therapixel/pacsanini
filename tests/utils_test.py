# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that resource files can correctly be read
if they have the good columns.
"""
import os

from unittest.mock import patch

import pandas as pd
import pytest

from click.testing import CliRunner

from pacsanini import config, utils
from pacsanini.errors import InvalidResourceFile
from pacsanini.models import QueryLevel


@pytest.mark.utils
def test_read_resources(tmpdir):
    """Test that resources can correctly be read."""
    patient_lvl_data = pd.DataFrame(
        {
            "PatientID": ["patient1", "patient2", "patient3"],
            "RandomCol": ["val1", "val2", "val3"],
        }
    )
    study_lvl_data = pd.DataFrame({"StudyInstanceUID": ["study1", "study2", "study3"]})

    pat_path = tmpdir.join("patients.csv")
    study_path = tmpdir.join("studies.csv")

    patient_lvl_data.to_csv(pat_path, index=False)
    study_lvl_data.to_csv(study_path, index=False)

    patients = utils.read_resources(pat_path, QueryLevel.PATIENT)
    assert patients == ["patient1", "patient2", "patient3"]

    studies = utils.read_resources(study_path, QueryLevel.STUDY)
    assert studies == ["study1", "study2", "study3"]

    with pytest.raises(InvalidResourceFile):
        utils.read_resources(pat_path, QueryLevel.STUDY)


@pytest.mark.cli
def test_is_db_uri():
    """Test that database URIs are correctly picked up."""
    db_uris = [
        "postgresql://foo:bar@localhost/mydatabase",
        "postgresql+psycopg2://foo:bar@localhost/mydatabase",
        "postgresql+pg8000://foo:bar@localhost/mydatabase",
        "mysql://foo:bar@localhost/foo",
        "mysql+mysqldb://foo:bar@localhost/foo",
        "oracle://foo:bar@127.0.0.1:1521/mydb",
        "sqlite:///foo.db",
    ]
    for uri in db_uris:
        assert utils.is_db_uri(uri) is True

    non_db_uris = ["/data/foo/bar.json", "sqlite.csv"]
    for uri in non_db_uris:
        assert utils.is_db_uri(uri) is False


@pytest.mark.utils
def test_default_config_path():
    """Test that the correct configuration file is returned when multiple
    options are available. The order should be: env var, current dir,
    home dir, None.
    """
    runner = CliRunner()

    mock_homedir_file = "homedir.yaml"
    mock_currentdir_file = "pacsaninirc.yaml"
    mock_envvar_file = "envvar.yaml"

    def touch(path):
        with open(path, "w") as f:
            f.write("")

    with runner.isolated_filesystem():
        with patch("pacsanini.utils.DEFAULT_SETTINGS_PATH", mock_homedir_file):
            os.environ[config.PACSANINI_CONF_ENVVAR] = mock_envvar_file
            touch(mock_homedir_file)
            touch(mock_currentdir_file)
            touch(mock_envvar_file)

            assert utils.default_config_path() == mock_envvar_file
            del os.environ[config.PACSANINI_CONF_ENVVAR]
            os.remove(mock_envvar_file)

            assert utils.default_config_path() == mock_currentdir_file
            os.remove(mock_currentdir_file)

            assert utils.default_config_path() == mock_homedir_file
            os.remove(mock_homedir_file)

            assert utils.default_config_path() is None
