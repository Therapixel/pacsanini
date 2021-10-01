# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The convert module provides utility methods that can be used
to convert raw DICOM data to DICOM files.
"""
import json
import re

from datetime import datetime, timedelta
from typing import Dict, Union

from pydicom import Dataset, dcmread


def str2datetime(dcm_date: str) -> datetime:
    """Parse a date in DICOM string format and return
    a datetime object.

    Strings can come in the following formats:
    YYYYMMDD (date), or YYYYMMDDHHMMSS.FFFFFF&ZZXX
    (datetime) -as specified by the DICOM standard.

    Parameters
    ----------
    dcm_date : str
        A date(time) in DICOM string format.

    Returns
    -------
    datetime
        A datetime corresponding to the DICOM string
        value.

    Raises
    ------
    ValueError
        A ValueError is raised if the dcm_date parameter
        does not conform to any DICOM date(time) format.
    """
    fmt = "%Y%m%d"
    try:
        return datetime.strptime(dcm_date, fmt)
    except ValueError:
        fmt += "%H%M%S.%f"
        try:
            return datetime.strptime(dcm_date, fmt)
        except ValueError:
            fmt += "%z"
            return datetime.strptime(dcm_date, fmt)


def str2timedelta(dcm_time: str) -> timedelta:
    """Parse a time in DICOM string value and return a
    timedelta object.

    Time strings in DICOM format are formatted in the
    following way: HHMMSS.FFFFFF. The only mandatory
    component in DICOM time strings is the hour component.

    Parameters
    ----------
    dcm_time : str
        A time value in DICOM string format.

    Returns
    -------
    timedelta
        The DICOM time value as a timedelta object.

    Raises
    ------
    ValueError
        A ValueError is raised if the dcm_time parameter
        does not conform to the DICOM time format.
    """
    m = re.fullmatch(
        r"(\d\d)(?:(\d\d)(?:(\d\d)(?:\.(\d{1,6}))?)?)?", dcm_time, flags=re.ASCII
    )

    if m is None:
        raise ValueError(f"Invalid DICOM time string: '{dcm_time}'")

    time_vals = {"hours": int(m.group(1))}
    if m.group(2) is not None:
        time_vals["minutes"] = int(m.group(2))
        if m.group(3) is not None:
            time_vals["seconds"] = int(m.group(3))
            if m.group(4) is not None:
                time_vals["microseconds"] = int(m.group(4).ljust(6, "0"))

    return timedelta(**time_vals)


def datetime2str(date_time: datetime, use_time: bool = False) -> str:
    """Convert a datetime object to a DICOM compliant date(time) string.

    Parameters
    ----------
    date_time : datetime
        The datetime object to convert ot a DICOM string.
    use_time : bool
        If False, the default, don't add the time component in the
        return value. Note that this has no impact if the datetime
        component has an existing time component.

    Returns
    -------
    str
        The datetime object as a DICOM string.
    """
    omit_time = (
        date_time.hour == 0
        and date_time.minute == 0
        and date_time.second == 0
        and date_time.microsecond == 0
    )

    if use_time or not omit_time:
        if date_time.tzinfo is not None:
            return date_time.strftime("%Y%m%d%H%M%S.%f%z")
        return date_time.strftime("%Y%m%d%H%M%S.%f")
    return date_time.strftime("%Y%m%d")


def timedelta2str(time_delta: timedelta) -> str:
    """Convert a timedelta object to its DICOM string counterpart.

    Parameters
    ----------
    time_delta : timedelta
        The timedelta object to convert to string.

    Returns
    -------
    str
        The timdelta objected represented as a DICOM time string.
    """
    ref_date = datetime(1970, 1, 1) + time_delta
    return ref_date.strftime("%H%M%S.%f")


def agestr2years(age_str: str) -> int:
    """Convert an Age String into a int where the age unit is
    in years. Expected formats are: nnnD, nnnW, nnnM, nnnY.

    Notes
    -----
    The return value may not yield precise results as the following
    assumptions are made: there are 365 days in a year, there are 52
    weeks in a year, and there are 12 months in a year.

    Parameters
    ----------
    age_str : str
        A DICOM Age String value.

    Returns
    -------
    int
        The number of years as an int.

    Raises
    ------
    ValueError
        A ValueError is raised if the age_str is not a valid
        Age String.
    """
    if not age_str or len(age_str) != 4:
        raise ValueError(
            f"Expected the age string to be in the 'nnn[DWMY]' format. Obtained: {age_str}"
        )
    age_unit = age_str[-1].upper()
    if age_unit not in "DWMY":
        raise ValueError(
            f"Expected the age string unit to be one of 'D', 'W', 'M', 'Y'. Obtained: {age_unit}"
        )

    age_value = age_str[:3]
    if age_unit == "D":
        return int(age_value) // 365
    elif age_unit == "W":
        return int(age_value) // 52
    elif age_unit == "M":
        return int(age_value) // 12
    else:
        return int(age_value)


def dcm2dict(
    dcm: Union[Dataset, bytes, str], include_pixels: bool = False
) -> Dict[str, dict]:
    """Return the JSON-compatiable dict representation of a DICOM file.

    Parameters
    ----------
    dcm : Union[Dataset, bytes, str]
        The DICOM Dataset, bytes, or file path to convert to use in order
        to produce the JSON dict.
    include_pixels : bool
        If True, include the pixel array in the generated dict. The default
        is False.

    Returns
    -------
    Dict[str, dict]
        A JSON-compatible dict representation of the DICOM.
    """
    if isinstance(dcm, (bytes, str)):
        dcm = dcmread(dcm, stop_before_pixels=not include_pixels)
    if not include_pixels:
        dcm.PixelData = None

    def tag2name(dcm: Dataset, tag: str) -> str:
        name = dcm[tag].name.replace("[", "").replace("]", "")
        name = "".join(char.capitalize() for char in name.split(" "))
        return name

    def dict2nameddict(dcm: Dataset, seq_dict: Dict[str, dict]):
        for key, value in seq_dict.items():
            value["Name"] = tag2name(dcm, key)
            if value["vr"] == "SQ" and len(value["Value"]):
                value["Value"][0] = dict2nameddict(dcm[key][0], value["Value"][0])
        return seq_dict

    dcm_dict = dcm.to_json_dict()
    for key, value in dcm_dict.items():
        value["Name"] = tag2name(dcm, key)
        if value["vr"] == "SQ" and len(value["Value"]):
            value["Value"][0] = dict2nameddict(dcm[key][0], value["Value"][0])
    return dcm_dict


def dict2dcm(dcm_dict: Dict[str, dict]) -> Dataset:
    """Convert a dictionary containing DICOM tag metadata to a DICOM Dataset.

    Parameters
    ----------
    dcm_dict : Dict[str, dict]
        A dictionary containg DICOM tag metadata that you want to
        convert to a Dataset.

    Returns
    -------
    Dataset
        The DICOM Dataset.
    """
    for values in dcm_dict.values():
        values.pop("Name", None)

    return Dataset.from_json(json.dumps(dcm_dict))
