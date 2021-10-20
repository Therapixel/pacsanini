# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The config modules provides classes that correspond the how the
pacsanini package is configured.
"""
import json
import os

from datetime import datetime, time, timedelta
from typing import List, Optional, Union

import yaml

from pydantic import BaseModel, root_validator, validator

from pacsanini.convert import datetime2str, str2datetime
from pacsanini.models import DicomNode, QueryLevel, StorageSortKey
from pacsanini.parse import DicomTag, DicomTagGroup


DEFAULT_CONFIG_NAME = "pacsaninirc.yaml"
DEFAULT_SETTINGS_PATH = os.path.join(os.path.expanduser("~"), DEFAULT_CONFIG_NAME)
PACSANINI_CONF_ENVVAR = "PACSANINI_CONFIG"


class EmailConfig(BaseModel):
    """A class to store email configuration settings.

    Attributes
    ----------
    username : Optional[str]
        The email account's name.
    password : Optional[str]
        The email account's password.
    host : Optional[str]
        The email server host.
    port : Optional[int]
        The port to send the email to.
    """

    username: Optional[str] = ""
    password: Optional[str] = ""
    host: Optional[str] = "smtp.gmail.com"
    port: Optional[int] = 465


class MoveConfig(BaseModel):
    """The MoveConfig class represents the possible settings that
    are used when querying for data.

    The start_time and end_time attributes correspond to the time
    in the day at which studies should be queried. This is to avoid
    saturating of a PACS node during business hours. A time
    instance or a string in the HH, HH:MM, or HH:MM:SS format are
    accepted. Hours should be in the 24 hour format.

    If the start_time is greater than the end_time, it is assumed
    that the queries should be performed over two days. For example,
    with start_time = "20:00" and end_time = "07:00", queries will
    run from 20:00 on day 1 until 07:00 on day 2.

    Attributes
    ----------
    start_time : Optional[time]
        The time of the day at which C-MOVE queries should start at.
        If set, the end_time parameter should be set as well.
    end_time : Optional[time]
        The time of the day at which C-MOVE queries should end at.
        If set, the start_time parameter should be set as well.
    query_level : QueryLevel
        The root model to use when querying for DICOM resources. The
        default is STUDY.
    """

    start_time: Optional[time] = None
    end_time: Optional[time] = None
    query_level: QueryLevel = QueryLevel.STUDY

    @root_validator(pre=True)
    def validate_start_and_end_time(
        cls, values
    ):  # pylint: disable=no-self-argument,no-self-use
        """Validate that both start_time and end_time
        are set or that both are unset.
        """
        start_time = values.get("start_time", None)
        end_time = values.get("end_time", None)
        if (start_time and not end_time) or (end_time and not start_time):
            msg = "Both start_time and end_time parameters must be set or both must be unset."
            raise ValueError(msg)

        def validate_format(val):
            if not val:
                return None
            if isinstance(val, time):
                return val

            return time.fromisoformat(val)

        start_time = validate_format(start_time)
        end_time = validate_format(end_time)
        if start_time == end_time:
            start_time, end_time = None, None

        values["start_time"] = start_time
        values["end_time"] = end_time
        return values

    def can_query(self) -> bool:
        """Return True if the current time of the day is between the
        specified start_time and end_time.
        """
        if self.start_time is None or self.end_time is None:
            return True

        now = self.now()
        today = now - timedelta(
            hours=now.hour,
            minutes=now.minute,
            seconds=now.second,
            microseconds=now.microsecond,
        )
        start_td = timedelta(
            hours=self.start_time.hour,
            minutes=self.start_time.minute,
            seconds=self.start_time.second,
            microseconds=self.start_time.microsecond,
        )
        end_td = timedelta(
            hours=self.end_time.hour,
            minutes=self.end_time.minute,
            seconds=self.end_time.second,
            microseconds=self.end_time.microsecond,
        )

        if self.end_time > self.start_time:
            upper_limit = today + end_td
            lower_limit = today + start_td
            return lower_limit < now < upper_limit

        return now > (today + start_td) or now < (today + end_td)

    def now(self) -> datetime:
        """Return the current datetime."""
        return datetime.now()

    class Config:
        use_enum_values = True
        json_encoders = {time: lambda time_: time_.isoformat(autospec="seconds")}


class NetConfig(BaseModel):
    """The NetConfig class represents the possible DICOM network
    configuration that can be made.

    Attributes
    ----------
    local_node : DicomNode
        The local DICOM node's information configuration.
    called_node : DicomNode
        The configuration settings for the DICOM node to call
        (eg: emit C-FIND, C-MOVE, or C-ECHO messages to).
    dest_node : DicomNode
        The destination node to send DICOM results from C-MOVE
        results to. If unset, this will be equal to the local_node.
    """

    local_node: DicomNode
    called_node: DicomNode
    dest_node: Optional[DicomNode] = None

    @validator("called_node")
    def validate_called_node(cls, v):  # pylint: disable=no-self-argument,no-self-use
        """Validate that the called has correct network information."""
        if bool(v.ip) is False or bool(v.port) is False:
            err_msg = (
                "The called DICOM node configuration must have a valid IP and port."
            )
            raise ValueError(err_msg)
        return v

    @root_validator(pre=True)
    def validate_dest_node(cls, values):  # pylint: disable=no-self-argument,no-self-use
        """Check if the provided dest_node value is None.
        If true, set the dest_node to be equal to the local_node.
        """
        if not values.get("dest_node"):
            values["dest_node"] = values["local_node"]
        return values


class FindConfig(BaseModel):
    """The FindConfig class is used to store settings that are
    to be used for sending C-FIND requests.

    Attributes
    ----------
    query_level : QueryLevel
        The query level to use when sending C-FIND messages. The
        default is STUDY.
    search_fields : List[str]
        A list of DICOM tag fields to obtain values from each
        returned result.
    start_date : datetime
        The date component of the query. Can be passed as a string
        in which case it should be in a valid DICOM date or datetime
        format (eg: YYYYMMDD).
    end_date : Optional[datetime]
        The upper date limit of the query. Can be passed as a string
        in which case it should be in a valid DICOM date or datetime
        format (eg: YYYYMMDD).
    modality : Optional[str]
        The modality to match for each query.
    """

    query_level: QueryLevel = QueryLevel.STUDY
    search_fields: List[str] = []
    start_date: datetime
    end_date: Optional[datetime] = None
    modality: Optional[str] = ""

    @validator("start_date", "end_date", pre=True)
    def validate_date(cls, v):  # pylint: disable=no-self-argument,no-self-use
        """Validate a date and accept string formats."""
        if isinstance(v, str):
            return str2datetime(v)
        return v

    class Config:
        use_enum_values = True
        json_encoders = {datetime: datetime2str}


class StorageConfig(BaseModel):
    """The StorageConfig indicates where DICOM files should be
    persisted as a result of launching C-MOVE requests or a
    C-STORESCP server.

    Attributes
    ----------
    resources : str
        The file path to store results from C-FIND results.
    resources_meta : str
        The file path to store results from parsing DICOM files.
    directory : str
        The directory path to persist DICOM files under.
    sort_by : str
        An indication of how to store received DICOM files.
        Accepted values are "PATIENT", "STUDY", and "IMAGE".
    """

    resources: str
    resources_meta: Optional[str] = "resources_meta.csv"
    directory: str
    sort_by: StorageSortKey = StorageSortKey.PATIENT

    class Config:
        use_enum_values = True


class PacsaniniConfig(BaseModel):
    """PacsaniniConfig represents the overall configuration
    file that can be used to conveniently run pacsanini
    functionalities.

    Attributes
    ----------
    find : Optional[FindConfig]
        The application's find configuration.
    move : Optional[MoveConfig]
        The application's move configuration.
    net : Optional[NetConfig]
        The application's network configuration.
    storage : Optional[StorageConfig]
        The application's storage configuration.
    tags : Optional[List[DicomTag]]
        The application's DICOM tags parsing configuration.
    email : Optional[EmailConfig]
        The application's email settings.
    """

    find: Optional[FindConfig] = None
    move: Optional[MoveConfig] = None
    net: Optional[NetConfig] = None
    storage: Optional[StorageConfig] = None
    tags: Optional[List[DicomTag]] = None
    email: Optional[EmailConfig] = EmailConfig()

    @classmethod
    def from_json(cls, path: str):
        """Obtain a PacsaniniConfig instance from a json file."""
        with open(path) as in_:
            content = json.load(in_)
        return cls(**content)

    @classmethod
    def from_yaml(cls, path: str):
        """Obtain a PacsaniniConfig instance from a yaml file."""
        with open(path) as in_:
            content = yaml.safe_load(in_.read())
        return cls(**content)

    def can_find(self) -> bool:
        """Return True if the current configuration is adequately
        set for emitting C-FIND requests -return False otherwise.
        """
        return self.net is not None and self.find is not None

    def can_move(self) -> bool:
        """Returns True if the move config, net config, and storage config
        is not None.
        """
        return (
            self.move is not None and self.net is not None and self.storage is not None
        )

    def can_parse(self) -> bool:
        """Returns True if the tags config is not None -False otherwise."""
        return self.tags is not None

    def get_tags(self) -> Union[DicomTagGroup, None]:
        """Return the DICOMTagGroup instance associated
        with the current configuration.
        """
        if self.tags is None:
            return None
        return DicomTagGroup(tags=[tag_grp.dict() for tag_grp in self.tags])
