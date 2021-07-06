# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that the convert module will yield expected and correct results for
all supported data types.
"""
from datetime import datetime, timedelta, timezone

import pytest

from pydicom import Dataset

from pacsanini import convert


@pytest.mark.convert
def test_str2datetime():
    """Test that date and datetime strings can correctly
    be converted to datetime objects.
    """
    date1 = "20011213"
    date1_expected = datetime(2001, 12, 13)
    date1_result = convert.str2datetime(date1)
    assert date1_result == date1_expected

    date2 = "20011213045801.000099"
    date2_expected = datetime(2001, 12, 13, 4, 58, 1, 99)
    date2_result = convert.str2datetime(date2)
    assert date2_result == date2_expected

    date3 = "20011213045801.000099+1200"
    date3_expected = datetime(
        2001, 12, 13, 4, 58, 1, 99, tzinfo=timezone(timedelta(seconds=43200))
    )
    date3_result = convert.str2datetime(date3)
    assert date3_result == date3_expected

    with pytest.raises(ValueError):
        convert.str2datetime("2012-01-13")

    with pytest.raises(ValueError):
        convert.str2datetime("20121403")


@pytest.mark.convert
def test_str2timedelta():
    """Test that converting DICOM time strings to timedelta
    objects functions correctly.
    """
    time1 = "04"
    time1_expected = timedelta(hours=4)
    time1_result = convert.str2timedelta(time1)
    assert time1_result == time1_expected

    time2 = "0458"
    time2_expected = timedelta(hours=4, minutes=58)
    time2_result = convert.str2timedelta(time2)
    assert time2_result == time2_expected

    time3 = "045812"
    time3_expected = timedelta(hours=4, minutes=58, seconds=12)
    time3_result = convert.str2timedelta(time3)
    assert time3_result == time3_expected

    time4 = "045812.000123"
    time4_expected = timedelta(hours=4, minutes=58, seconds=12, microseconds=123)
    time4_result = convert.str2timedelta(time4)
    assert time4_result == time4_expected

    time5 = "045812.9"
    time5_expected = timedelta(hours=4, minutes=58, seconds=12, microseconds=900000)
    time5_result = convert.str2timedelta(time5)
    assert time5_result == time5_expected

    time5 = "045812.0987"
    time5_expected = timedelta(hours=4, minutes=58, seconds=12, microseconds=98700)
    time5_result = convert.str2timedelta(time5)
    assert time5_result == time5_expected

    invalid_times = [
        "045812000123",
        "021",
        "0",
        "0458120001231213",
        "012345.",
        "01.123",
        "0123.45",
    ]
    for time_str in invalid_times:
        with pytest.raises(ValueError):
            convert.str2timedelta(time_str)


@pytest.mark.convert
def test_datetime2str():
    """Test that converting datetime objects to string
    values is done correctly.
    """
    date1 = datetime(
        2001, 12, 13, 4, 58, 1, 99, tzinfo=timezone(timedelta(seconds=43200))
    )
    date1_expected = "20011213045801.000099+1200"
    date1_result = convert.datetime2str(date1)
    assert date1_result == date1_expected

    date2 = datetime(2001, 12, 13, 4, 58, 1, 99)
    date2_expected = "20011213045801.000099"
    date2_result = convert.datetime2str(date2)
    assert date2_result == date2_expected

    date3 = datetime(2001, 12, 13)
    date3_expected = "20011213"
    date3_result = convert.datetime2str(date3)
    assert date3_result == date3_expected

    date3bis_expected = "20011213000000.000000"
    date3bis_result = convert.datetime2str(date3, use_time=True)
    assert date3bis_result == date3bis_expected


@pytest.mark.convert
def test_timedelta2str():
    """Test that converting a timedelta object to a string
    functions correctly.
    """
    tdelta = timedelta(hours=20, minutes=23)
    td_expected = "202300.000000"
    td_result = convert.timedelta2str(tdelta)
    assert td_result == td_expected


@pytest.mark.convert
def test_double_conversion():
    """Test that converting a string to datetime and then
    back to a string gives a consistent result.
    """
    date = "20130120"
    result = convert.datetime2str(convert.str2datetime(date))
    assert result == date


@pytest.mark.convert
def test_dcm2dict(dicom_path: str, dicom: Dataset):
    """Test that converting a DICOM file to a dict can correctly
    be done.
    """
    dcm_dict = convert.dcm2dict(dicom_path)
    assert isinstance(dcm_dict, dict)

    dcm = convert.dict2dcm(dcm_dict)
    assert isinstance(dcm, Dataset)

    assert dcm.SOPInstanceUID == dicom.SOPInstanceUID
