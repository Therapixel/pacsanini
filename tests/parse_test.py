# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
# pylint: disable=redefined-outer-name
"""Test that parsing DICOM tags can be done using all the available methods. This is
the core testing module for DICOM parsing so it should be treated with great attention.
"""
import os

from typing import Generator

import pandas as pd
import pydicom
import pytest

from pandas.testing import assert_frame_equal

from pacsanini import parse


@pytest.fixture
def tags2parse():
    """Return instructions on DICOM tags to parse."""
    return [
        {"tag_name": "ImageLaterality", "default_val": "NOT_SET"},
        parse.DicomTag(tag_name=["SopInstanceUUUUID", "SOPInstanceUID"]),
        {"tag_name": ["SopClazzUUID", "SOPClassUID"], "callback": lambda x: "foobar"},
        parse.DicomTag(tag_name=["StudyInstanceUID"], tag_alias="study_uid"),
    ]


@pytest.fixture
def tags2parse_results(dicom):
    """Return the expected results that the tags2parse
    fixture should return for the dicom fixture.
    """
    return {
        "ImageLaterality": "L",
        "SopInstanceUUUUID": dicom.SOPInstanceUID,
        "SopClazzUUID": "foobar",
        "study_uid": dicom.StudyInstanceUID,
    }


@pytest.mark.parse
def test_get_dicom_tag_value(dicom: pydicom.FileDataset):
    """Test that a DICOM tag value is returned correctly."""
    image_uid = parse.get_dicom_tag_value(dicom, "SOPInstanceUID")
    assert image_uid == dicom.SOPInstanceUID

    def rand_val(_):
        return "foobar"

    image_uid = parse.get_dicom_tag_value(dicom, "SOPInstanceUID", callback=rand_val)
    assert image_uid == "foobar"

    new_value = parse.get_dicom_tag_value(dicom, "NonExistent.Tag")
    assert new_value is None

    # parse a nested tag without callback
    new_value = parse.get_dicom_tag_value(dicom, "ViewCodeSequence.CodeValue")
    assert new_value == "R-10226"

    # parse a nested tag with callback
    new_value = parse.get_dicom_tag_value(
        dicom, "ViewCodeSequence.CodeValue", callback=rand_val
    )
    assert new_value == "foobar"


@pytest.mark.parse
def test_get_tag_value(dicom: pydicom.FileDataset):
    """Test that getting a tag value does its job as expected."""
    image_uid = parse.get_tag_value(dicom, tag_name="SOPInstanceUID")
    assert image_uid == dicom.SOPInstanceUID

    image_uid = parse.get_tag_value(dicom, ["ImageUID", "SOPInstanceUID"])
    assert image_uid == dicom.SOPInstanceUID

    def rand_val(_):
        return "foobar"

    image_uid = parse.get_tag_value(dicom, "SOPInstanceUID", callback=rand_val)
    assert image_uid == "foobar"

    new_value = parse.get_tag_value(
        dicom, ["MyTag", "Unknown.Still"], callback=rand_val, default_val="NOT_FOUND"
    )
    assert new_value == "NOT_FOUND"

    tag = parse.DicomTag(tag_name="SOPInstanceUID")
    image_uid = tag.tag_value(dicom)
    assert image_uid == dicom.SOPInstanceUID


@pytest.mark.parse
def test_parse_dicom(
    dicom_path: str,
    dicom: pydicom.FileDataset,
    tags2parse: dict,
    tags2parse_results: dict,
):
    """Test that parsing an entire DICOM is correctly done."""
    results_with_path = parse.parse_dicom(dicom_path, tags2parse)
    results_with_dicom = parse.parse_dicom(dicom, tags2parse)
    assert results_with_path == results_with_dicom == tags2parse_results

    tag_group = parse.DicomTagGroup(tags=tags2parse)
    assert tag_group.parse_dicom(dicom) == tags2parse_results


@pytest.mark.parse
def test_parse_dicoms(
    dicom_path: str,
    dicom: pydicom.FileDataset,
    tags2parse: dict,
    tags2parse_results: dict,
):
    """Test that parsing multiple DICOM files is correctly done."""
    results = parse.parse_dicoms([dicom_path, dicom], tags2parse)
    assert isinstance(results, Generator)
    results = list(results)

    expected = [tags2parse_results, tags2parse_results]
    assert results == expected

    tag_group = parse.DicomTagGroup(tags=tags2parse)
    assert list(tag_group.parse_dicoms([dicom_path, dicom])) == expected


@pytest.mark.parse
def test_parse_dicoms2df(
    dicom_path: str,
    dicom: pydicom.FileDataset,
    tags2parse: dict,
    tags2parse_results: dict,
):
    """Test that parsing DICOMs to a data frame yields the expected
    results.
    """
    tag_group = parse.DicomTagGroup(tags=tags2parse)
    results = tag_group.parse_dicoms2df([dicom_path, dicom])
    assert isinstance(results, pd.DataFrame)

    expected = pd.DataFrame([tags2parse_results, tags2parse_results])
    assert_frame_equal(results, expected)


@pytest.mark.parse
def test_dicom_tag_group(data_dir: str):
    """Test that constructors are ok."""
    json_conf = os.path.join(data_dir, "tags_conf.json")
    yaml_conf = os.path.join(data_dir, "tags_conf.yaml")

    tag_group_json = parse.DicomTagGroup.from_json(json_conf)
    tag_group_yaml = parse.DicomTagGroup.from_yaml(yaml_conf)

    assert isinstance(tag_group_json, parse.DicomTagGroup)
    assert isinstance(tag_group_yaml, parse.DicomTagGroup)

    assert tag_group_json == tag_group_yaml
