# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The models module provide data structures for the net module so that
DICOM network nodes can easily be represented.
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, validator


class DicomNode(BaseModel):
    """DicomNode represents a networking node in a DICOM system.

    Attributes
    ----------
    aetitle : bytes
        The DICOM node's AE Title. When initialized, this can be a string.
    ip : Optional[str]
        The DICOM node's IP address or hostname. Defaults to None.
    port : Optional[int]
        The DICOM node's listening port. When initialized, the port value
        can be a string value.
    has_net_info : Optional[bool]
        If the ip and port attributes are not None, has_net_info is set
        to True -otherwise this is False.
    """

    aetitle: bytes
    ip: Optional[str] = None
    port: Optional[int] = None
    has_net_info: Optional[bool] = False

    @validator("aetitle", pre=True)
    def validate_aetitle(cls, v):  # pylint: disable=no-self-argument,no-self-use
        """Coerce the aetitle to bytes."""
        if isinstance(v, bytes):
            return v
        if isinstance(v, str):
            return v.encode()
        raise ValueError(f"aetitle must be a str or bytes -obtained ({type(v)}): {v}")

    @validator("ip", pre=True)
    def validate_ip(cls, v):  # pylint: disable=no-self-argument,no-self-use
        """Validate the IP address."""
        return v if v else None

    @validator("port", pre=True)
    def validate_port(cls, v):  # pylint: disable=no-self-argument,no-self-use
        """Coerce str to int if need be."""
        if not v:
            return None
        if isinstance(v, str):
            return int(v)
        return v

    @validator("has_net_info", pre=True, always=True)
    def validate_net_info(
        cls, v, values, **kwargs
    ):  # pylint: disable=no-self-argument,no-self-use,unused-argument
        """Check if the IP and port parameters are given."""
        return (
            values.get("ip", None) is not None and values.get("port", None) is not None
        )

    def has_port(self) -> bool:
        """Returns True if the port for the application is set, False otherwise."""
        return self.port is not None

    class Config:
        json_encoders = {bytes: lambda v: v.encode()}


class QueryLevel(str, Enum):
    """QueryLevel provides abstraction over the specific
    query level that users want.
    """

    PATIENT = "PATIENT"
    STUDY = "STUDY"


class StorageSortKey(str, Enum):
    """StorageSortKey indicates how to organize DICOM files
    when persisting them in the context of a storescp server.
    """

    PATIENT = "PATIENT"
    STUDY = "STUDY"
    IMAGE = "IMAGE"
