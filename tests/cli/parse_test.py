# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that the parsing functionalities of the pacsanini package can be
correctly accessed from the command line.
"""
import json
import os

import pytest
import yaml

from click.testing import CliRunner

from pacsanini.cli.parse import gen_parser, parse
from pacsanini.parse import DicomTagGroup


@pytest.fixture()
def sqlparse_conf(tmpdir: str) -> str:
    sql_path = f"sqlite:///{os.path.join(str(tmpdir), 'test.sqlite')}"
    conf = {
        "storage": {
            "directory": "foobar",
            "resources_meta": "test.csv",
            "resources": sql_path,
        }
    }
    conf_path = os.path.join(str(tmpdir), "conf.yaml")
    with open(conf_path, "w") as out:
        yaml.dump(conf, out)

    return conf_path


@pytest.mark.cli
def test_parse(data_dir):
    """Test that the parsing commands functions correctly."""
    runner = CliRunner()
    result_csv = runner.invoke(
        parse,
        [
            "-i",
            os.path.join(data_dir, "dicom-files"),
            "-f",
            os.path.join(data_dir, "tags_conf.yaml"),
            "--fmt",
            "csv",
        ],
    )
    assert result_csv.exit_code == 0
    assert len(result_csv.output) > 0
    assert ",dicom_path" in result_csv.output

    result_json = runner.invoke(
        parse,
        [
            "-i",
            os.path.join(data_dir, "dicom-files"),
            "-f",
            os.path.join(data_dir, "tags_conf.json"),
            "--fmt",
            "json",
            "--exclude-path",
        ],
    )
    assert result_json.exit_code == 0
    assert len(result_json.output) > 0
    assert '"dicom_path"' not in result_json.output

    result_invalid = result_json = runner.invoke(
        parse,
        [
            "-i",
            os.path.join(data_dir, "dicom-files"),
            "-f",
            os.path.join(data_dir, "tags_conf"),
            "--fmt",
            "json",
        ],
    )
    assert result_invalid.exit_code != 0


@pytest.mark.cli
def test_parse_sql(data_dir, sqlparse_conf):
    """Test that the parsing command functions correctly for sql."""
    runner = CliRunner()
    result_sql = runner.invoke(
        parse,
        [
            "-i",
            os.path.join(data_dir, "dicom-files"),
            "-f",
            sqlparse_conf,
            "--fmt",
            "sql",
        ],
    )
    assert result_sql.exit_code == 0


@pytest.mark.cli
def test_parse_conf():
    """Test that generating a configuration file functions
    correctly.
    """
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(gen_parser, ["-o", "test_conf.json"], input="\n")
        assert result.exit_code != 0

    with runner.isolated_filesystem():
        result = runner.invoke(
            gen_parser,
            ["-o", "test_conf.json"],
            input="\n".join(
                [
                    "StudyInstanceUID",  # base tag
                    "SOPClassUID",  # tag alternative
                    "",  # move on
                    "study_uid",  # tag alias
                    "NOT_SET",
                    "y",  # add a second tag
                    "StudyDate",  # tag name
                    "",  # no alternative tag
                    "",  # no tag alias
                    "",  # no default value
                    "N",  # no new tag to add
                ]
            ),
        )
        assert result.exit_code == 0

        assert os.path.exists("test_conf.json")
        expected = {
            "tags": [
                {
                    "tag_name": ["StudyInstanceUID", "SOPClassUID"],
                    "tag_alias": "study_uid",
                    "default_val": "NOT_SET",
                },
                {"tag_name": "StudyDate", "tag_alias": "StudyDate"},
            ]
        }

        with open("test_conf.json") as in_:
            results = json.load(in_)
        assert results == expected
        # Check that the result is in synch with the model.
        assert DicomTagGroup(**results)
