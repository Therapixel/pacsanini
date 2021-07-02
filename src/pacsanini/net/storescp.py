# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The storescp module provides methods and classes that can be used to
instantiate and run storescp server instances. In addition, custom DICOM
event status responses are defined: UNABLE_TO_DECODE (0xC215) and
UNABLE_TO_PROCESS (0xC216).
"""
import os

from functools import partial
from typing import Callable, List, Tuple, Union
from warnings import filterwarnings

from loguru import logger
from pydicom import Dataset
from pynetdicom import AE, AllStoragePresentationContexts, evt
from pynetdicom.events import Event, InterventionEvent
from pynetdicom.status import Status

from pacsanini.models import DicomNode, StorageSortKey


filterwarnings(
    action="ignore",
    message="Starting in pydicom 3.0, Dataset.file_meta must be a FileMetaDataset class instance",
)

Status.add("UNABLE_TO_DECODE", 0xC215)
Status.add("UNABLE_TO_PROCESS", 0xC216)


def default_store_handle(
    event: Event, data_dir: str = "", sort_by: StorageSortKey = StorageSortKey.PATIENT
) -> int:
    """Handle a C-STORE request event by writing the received DICOM file
    to the data_dir in the way specified by sort_by.

    Parameters
    ----------
    event : Event
        The C-STORE event to handle.
    data_dir : str
        The directory to write results under.
    sort_by : StorageSortKey
        The organization to follow when writing DICOM files to disk.

    Returns
    -------
    int
        The reception status.
    """
    try:
        ds: Dataset = event.dataset
        ds.file_meta = event.file_meta
    except:  # pylint: disable=bare-except
        return Status.UNABLE_TO_DECODE  # pylint: disable=no-member

    if StorageSortKey.PATIENT == sort_by:
        dest = os.path.join(
            data_dir,
            ds.PatientID,
            ds.StudyInstanceUID,
            ds.SeriesInstanceUID,
            ds.SOPInstanceUID,
        )
    elif StorageSortKey.STUDY == sort_by:
        dest = os.path.join(
            data_dir, ds.StudyInstanceUID, ds.SeriesInstanceUID, ds.SOPInstanceUID
        )
    else:
        dest = os.path.join(data_dir, ds.SOPInstanceUID)
    dest += ".dcm"

    try:
        dcm_dir = os.path.dirname(dest)
        if dcm_dir:
            os.makedirs(dcm_dir, exist_ok=True)
        ds.save_as(dest, write_like_original=False)
        logger.info(f"{ds.SOPInstanceUID} is persisted.")
    except OSError:
        return Status.UNABLE_TO_PROCESS  # pylint: disable=no-member

    return 0x0000


class StoreSCPServer:
    """The StoreSCPServer class provides a way to run a storescp server
    that can be used to receive DICOM files and write them locally.

    Attributes
    ----------
    node : Union[DicomNode, dict]
        The DICOM node information to use when running the server.
    data_dir : str
        The path to the top-level directory where DICOM files should
        be written to. The default is the current directory.
    sort_by : StorageSortKey
        The method by which DICOM files should be written to disk.
    handlers : List[Tuple[InterventionEvent, Callable]]
        The methods to call each time an event is triggered. If unset,
        the default handler will be used.
    """

    def __init__(
        self,
        node: Union[DicomNode, dict],
        data_dir: str = "",
        sort_by: StorageSortKey = StorageSortKey.PATIENT,
        handlers: List[Tuple[InterventionEvent, Callable]] = None,
    ):
        if isinstance(node, dict):
            node = DicomNode(**node)
        if not node.has_port():
            raise ValueError(f"{node} must have a set port to listen to.")

        self.node = node
        self.data_dir = data_dir
        self.sort_by = sort_by

        self.using_default = False
        if handlers is None:
            default_handler = partial(
                default_store_handle, data_dir=self.data_dir, sort_by=self.sort_by
            )
            handlers = [(evt.EVT_C_STORE, default_handler)]
            self.using_default = True
        self.handlers = handlers

        self.scp = None

    def __enter__(self):
        self.run(block=False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self.node} - {self.data_dir}>"

    def run(self, block: bool = False):
        """Run the storescp server in a non-blocking way."""
        if self.scp is not None:
            raise RuntimeError(f"A current SCP instance is already running for {self}.")
        ae = AE(ae_title=self.node.aetitle)
        ae.supported_contexts = AllStoragePresentationContexts

        if self.using_default and self.data_dir:
            os.makedirs(self.data_dir, exist_ok=True)

        logger.debug(f"Starting SCP server: {self}")
        if not block:
            self.scp = ae.start_server(
                ("", self.node.port),
                block=False,
                evt_handlers=self.handlers,
                ae_title=self.node.aetitle,
            )
        else:
            ae.start_server(
                ("", self.node.port),
                block=True,
                evt_handlers=self.handlers,
                ae_title=self.node.aetitle,
            )

    def shutdown(self):
        """Shutdown the running scp server."""
        if self.scp is not None:
            logger.debug(f"Stopping SCP server: {self}")
            self.scp.shutdown()
            self.scp = None


def run_server(
    node: Union[DicomNode, dict],
    data_dir: str = "",
    sort_by: StorageSortKey = StorageSortKey.PATIENT,
    handlers=None,
    block: bool = False,
) -> Union[StoreSCPServer, None]:
    """Instantiate and run a storescp server using the provided
    configuration. The server will run in a detached thread.

    node : Union[DicomNode, dict]
        The DICOM node information to use when running the server.
    data_dir : str
        The path to the top-level directory where DICOM files should
        be written to. The default is the current directory.
    sort_by : StorageSortKey
        The method by which DICOM files should be written to disk.
    handlers : List[Tuple[InterventionEvent, Callable]]
        The methods to call each time an event is triggered. If unset,
        the default handler will be used.
    block : bool
        If False, the default, run the storescp server in a different
        thread. If True, the running server will block the current
        thread. In this case, a KeyboardInterrupt is needed to stop
        the server.

    Returns
    -------
    Union[StoreSCPServer, None]
        The running StoreSCPServer instance if block is set to False
        (in which case you must subsequently call the shudown method)
        or None if the server is in blocking mode.
    """
    server = StoreSCPServer(node, data_dir=data_dir, sort_by=sort_by, handlers=handlers)
    if block:
        server.run(block=True)
        return None

    server.run(block=False)
    return server
