# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that the parsing DICOM tags and persisting results to JSON format
can be correctly done.
"""
import json
import os

import pandas as pd
import pytest

from pandas.testing import assert_frame_equal

from pacsanini.io.io_parsers import parse_dir2json


@pytest.mark.io
def test_json_parser(tmp_path, data_dir, tag_group):
    """Test that parsing DICOM files to JSON yields correct results."""
    dest_path = str(tmp_path.joinpath("results.json"))
    parse_dir2json(
        os.path.join(data_dir, "dicom-files"), tag_group, dest_path, include_path=True
    )

    assert os.path.exists(dest_path)

    with open(dest_path) as in_:
        results_json = json.load(in_)
    results_df = (
        pd.DataFrame(results_json["dicom_tags"])
        .sort_values("SOPInstanceUID")
        .reset_index(drop=True)
    )
    assert "dicom_path" in results_df
    results_df.drop(columns="dicom_path", inplace=True)

    expected_path = os.path.join(data_dir, "dicom-results", "dicom_tags.json")
    with open(expected_path) as in_:
        expected_json = json.load(in_)
    expected_df = (
        pd.DataFrame(expected_json["dicom_tags"])
        .sort_values("SOPInstanceUID")
        .reset_index(drop=True)
    )

    assert_frame_equal(results_df, expected_df)
