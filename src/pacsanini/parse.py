# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The parse module contains the core methods and classes of the pacsanini
package that are used to obtain DICOM tag values from files.
"""
import json
import re

from contextlib import suppress
from typing import Any, Callable, Dict, Generator, Iterable, List, Optional, Union

import pandas as pd
import yaml

from pydantic import BaseModel, validator
from pydicom import dcmread
from pydicom.dataset import Dataset


_SEQUENCE = re.compile(r"\w+\[(\d)\]\w+")


def get_dicom_tag_value(
    data: Dataset, tag_name: str, *, callback: Callable[[Any], Any] = None
) -> Any:
    """Get the tag value of a particular DICOM tag. If the DICOM
    tag could not be found, None is returned. Nested tags can also
    be retrieved -to do so, use the dot notation to indicate
    the nested tag to retrieve.

    Tag names can have the following structures:
    * if the tag is found at the top level of the DICOM structure,
      its name suffices (eg: "SOPInstanceUID").
    * if the tag is nested, you can use the following structure:
      "<tag name>.<nested tag name>" (eg: "ViewCodeSequence.CodeValue").
      You can access as many nested tags as you want. Using the dot
      separator will always cause the method to read the first element
      of the DICOM sequence.
    * if the tag is nested and the nested tag is not in the sequence's
      first element, you can use the bracket notation "<tag name>[1]<nested tag name>"
      (eg: "DeidentificationMethodCodeSequence[1]CodingSchemeDesignator").
      Index errors will lead to None being returned.

    Parameters
    ----------
    data : Dataset
        The DICOM data element to search in.
    tag_name : str
        The name of the DICOM tag. This can be a nested tag.
    callback : Callable[[Any], Any]
        A callback function to use to format the obtained DICOM
        tag value.

    Returns
    -------
    Any
        The DICOM tag value or None if it was not found.
    """
    match = _SEQUENCE.search(tag_name)
    if "." in tag_name or match:
        if "." in tag_name:
            tag, sub_tag = tag_name.split(".", 1)
            seq_idx = 0
        else:
            tag = tag_name[: match.start(1) - 1]
            sub_tag = tag_name[match.end(1) + 1 :]
            seq_idx = int(match.group(1))

        try:
            seq = data.data_element(tag)
            if seq is None or seq.VM == 0:
                # ValueMultiplicity set to 0 indicates an invalid sequence.
                return None
            return get_dicom_tag_value(seq[seq_idx], sub_tag, callback=callback)
        except (KeyError, IndexError):
            return None

    try:
        data_el = data.data_element(tag_name)
    except KeyError:
        data_el = None
    else:
        data_el = data_el.value if data_el is not None else None
        if callback is not None and data_el is not None:
            with suppress(Exception):
                data_el = callback(data_el)

    return data_el


def get_tag_value(
    data: Dataset,
    tag_name: Union[Iterable[str], str],
    *,
    callback: Callable[[Any], Any] = None,
    default_val: Any = None,
) -> Any:
    """Get the tag value of a particular DICOM tag. If the DICOM
    tag could not be found, None is returned. Nested tags can also
    be retrieved -to do so, use the dot notation to indicate
    the nested tag to retrieve.

    Parameters
    ----------
    data : Dataset
        The DICOM data element to search in.
    tag_name : str
        The name of the DICOM tag. This can be a nested tag.
    callback : Callable[[Any], Any]
        A callback function to use to format the obtained DICOM
        tag value.
    default_val : Any
        The default value to return if the tag value
        could not be retrieved.

    Returns
    -------
    Any
        The DICOM tag value or None/the default value
        if it was not found.
    """
    tags_to_check = [tag_name] if isinstance(tag_name, str) else tag_name
    for tag in tags_to_check:
        tag_val = get_dicom_tag_value(data, tag, callback=callback)
        if tag_val:
            return tag_val

    if tag_val is None and default_val is not None:
        tag_val = default_val
    return tag_val


_builtin_types = {
    "str": str,
    "int": int,
    "float": float,
    "complex": complex,
    "bool": bool,
    "bytes": bytes,
    "bytearray": bytearray,
    "list": list,
    "set": set,
    "frozenset": frozenset,
    "dict": dict,
}


class DicomTag(BaseModel):
    """The DicomTag class represents a DICOM tag that you wish
    to obtain a tag value from.

    Attributes
    ----------
    tag_name : Union[List[str], str]
        A string or list of strings corresponding to a tag to
        parse.
    tag_alias : Optional[str]
        An alternative name to give to the tag after it is
        parsed.
    default_val : Optional[Any]
        If set and the tag_name did not find an existing value,
        return the default_val.
    callback : Optional[Callable[[Any], Any]]
        If set, use the callback method to format the parsed
        DICOM tag result.
    """

    tag_name: Union[List[str], str]
    tag_alias: Optional[str] = ""
    default_val: Optional[Any] = None
    callback: Optional[Callable[[Any], Any]] = None

    @validator("tag_alias", pre=True, always=True)
    def validate_alias(cls, v, values):  # pylint: disable=no-self-argument,no-self-use
        """Check for a tag alias. If not present, use the first
        tag_name value.
        """
        if v:
            return v

        tag_name = values["tag_name"]
        if isinstance(tag_name, str):
            return tag_name
        return tag_name[0]

    @validator("callback", pre=True)
    def validate_callback(cls, v):  # pylint: disable=no-self-argument,no-self-use
        """Validate the callback and load the method if
        it is a string.
        """
        if v is None or not isinstance(v, str):
            return v

        if ":" in v:
            from_imp, func = v.rsplit(":", 1)
            module = __import__(from_imp, fromlist=[""])
            v = getattr(module, func)
        else:
            v = _builtin_types[v]
        return v

    def tag_value(self, data: Dataset) -> Any:
        """Return the tag value of the given DICOM data."""
        return get_tag_value(
            data, self.tag_name, callback=self.callback, default_val=self.default_val
        )


def parse_dicom(
    dicom: Union[str, Dataset], tags: Iterable[Union[dict, DicomTag]]
) -> Dict[str, Any]:
    """Parse a DICOM file using the requirements specified
    by the tags.

    If the tags parameter is an iterable of dict instances,
    they will be coerced to DicomTag instances.

    Parameters
    ----------
    dicom : Union[str, Dataset]
        The DICOM file to parse.
    tags : Iterable[Union[dict, DicomTag]]
        The tags to get the values of from the DICOM file.

    Returns
    -------
    Dict[str, Any]
        A dict whose keys correspond to the tag aliases
        and whose values correspond to the DICOM tags' values.
    """
    if isinstance(dicom, str):
        dicom = dcmread(dicom, stop_before_pixels=True)

    results = {}
    for tag in tags:
        if isinstance(tag, dict):
            tag = DicomTag(**tag)
        results[str(tag.tag_alias)] = tag.tag_value(dicom)

    return results


def parse_dicoms(
    dicoms: Iterable[Union[str, Dataset]], tags: Iterable[Union[dict, DicomTag]]
) -> Generator[Dict[str, Any], None, None]:
    """Parse multiple DICOM files using the specified
    tags.

    Parameters
    ----------
    dicoms : Iterable[Union[str, Dataset]]
        The DICOM file to parse.
    tags : Iterable[Union[dict, DicomTag]]
        The tags to get the values of from the DICOM file.

    Yields
    ------
    Generator[Dict[str, Any], None, None]
        Dicts whose keys correspond to the tag aliases
        and whose values correspond to the DICOM tags' values.
    """
    for dcm in dicoms:
        yield parse_dicom(dcm, tags)


class DicomTagGroup(BaseModel):
    """Parse a group of DICOM tags."""

    tags: List[DicomTag]

    @classmethod
    def from_json(cls, path: str):
        """Obtain a DicomTagGroup instance from a json file."""
        with open(path) as in_:
            content = json.load(in_)
        return cls(**content)

    @classmethod
    def from_yaml(cls, path: str):
        """Obtain a DicomTagGroup instance from a yaml file."""
        with open(path) as in_:
            content = yaml.safe_load(in_.read())
        return cls(**content)

    def parse_dicom(self, dicom: Union[str, Dataset]) -> Dict[str, Any]:
        """Parse a DICOM file using the instance's tags."""
        return parse_dicom(dicom, self.tags)

    def parse_dicoms(
        self, dicoms: Iterable[Union[str, Dataset]]
    ) -> Generator[Dict[str, Any], None, None]:
        """Parse multiple DICOM files using the instance's tags."""
        for result in parse_dicoms(dicoms, self.tags):
            yield result

    def parse_dicoms2df(self, dicoms: Iterable[Union[str, Dataset]]) -> pd.DataFrame:
        """Parse multiple DICOM files using the instance's tags
        and return a DataFrame.
        """
        return pd.DataFrame(self.parse_dicoms(dicoms))
