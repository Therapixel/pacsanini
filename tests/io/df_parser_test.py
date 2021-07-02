# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that parsing DICOM files and returning results as a data frame
can be done correctly.
"""
import pandas as pd
import pytest

from pacsanini.io.df_parser import parse_dir2df


@pytest.mark.io
def test_df_parser(data_dir, tag_group):
    """Test that parsing DICOM files to DF yields correct results."""
    result = parse_dir2df(data_dir, tag_group, include_path=True)

    assert isinstance(result, pd.DataFrame)
