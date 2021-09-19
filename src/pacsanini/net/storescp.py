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
from typing import Any, Callable, Dict, List, Union
from warnings import simplefilter

from loguru import logger
from pydicom import Dataset
from pynetdicom import AE, AllStoragePresentationContexts, evt
from pynetdicom.events import Event
from pynetdicom.status import Status
from sqlalchemy import exc
from sqlalchemy.orm import Session

from pacsanini.db.crud import add_image, update_retrieved_study
from pacsanini.models import DicomNode, StorageSortKey


# Ignore 'Starting in pydicom 3.0, Dataset.file_meta must be a FileMetaDataset class instance'
# as long as we stay on pydicom 2.X
simplefilter("ignore", category=DeprecationWarning)

Status.add("UNABLE_TO_DECODE", 0xC215)
Status.add("UNABLE_TO_PROCESS", 0xC216)
Status.add("UNABLE_TO_RECORD", 0xC217)


def default_store_handle(
    event: Event,
    data_dir: str = "",
    sort_by: StorageSortKey = StorageSortKey.PATIENT,
    db_session: Session = None,
    callbacks: List[Callable[[Any], Any]] = None,
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
    callbacks : List[Callable[[Any], Any]]
        If supplied pass the received DICOM file to the callable as
        a positional argument (the first one) to each one of the
        callables for processing.

    Returns
    -------
    int
        The reception status.
    """
    try:
        ds: Dataset = event.dataset
        ds.file_meta = event.file_meta
    except:  # pylint: disable=bare-except
        logger.warning("Unable to decode received DICOM")
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
        os.makedirs(dcm_dir, exist_ok=True)
        ds.save_as(dest, write_like_original=False)
        logger.info(f"{ds.SOPInstanceUID} is persisted.")
    except OSError:
        logger.warning(f"Failed to write {ds.StudyInstanceUID} to disk")
        return Status.UNABLE_TO_PROCESS  # pylint: disable=no-member

    if db_session is not None:
        try:
            add_image(db_session, ds, filepath=dest)
            update_retrieved_study(db_session, ds.StudyInstanceUID)
        except exc.SQLAlchemyError as err:
            logger.warning(f"Failed to update database due to {err}")
            return Status.UNABLE_TO_RECORD  # pylint: disable=no-member

    if callbacks is not None:
        for func in callbacks:
            func(ds)

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
    db_session : Session
        Optional. If specified, received studies will be parsed and
        persisted to the provided database. The default is None.
    callbacks : List[Callable[[Any], Any]]
        If set, pass a list of callables that will be called on the
        DICOM file after it is received and persisted to disk.
    """

    def __init__(
        self,
        node: Union[DicomNode, dict],
        data_dir: str = "",
        sort_by: StorageSortKey = StorageSortKey.PATIENT,
        db_session: Session = None,
        callbacks: List[Callable[[Any], Any]] = None,
    ):
        if isinstance(node, dict):
            node = DicomNode(**node)
        if not node.has_port():
            raise ValueError(f"{node} must have a set port to listen to.")

        self.node = node
        self.data_dir = data_dir
        self.sort_by = sort_by

        kwargs: Dict[str, Any] = {"data_dir": self.data_dir, "sort_by": self.sort_by}
        if db_session is not None:
            kwargs["db_session"] = db_session
        if callbacks is not None:
            kwargs["callbacks"] = callbacks

        handler = partial(default_store_handle, **kwargs)
        handlers = [(evt.EVT_C_STORE, handler)]
        self.handlers = handlers

        self.scp = None

    def __enter__(self):
        self.run(block=False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.warning(f"Shutting down server due to {exc_type}")
            logger.warning(f"Exception value: {exc_val}")
            logger.warning(f"Exception traceback: {exc_tb}")
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

        if self.data_dir:
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
    callbacks: List[Callable[[Any], Any]] = None,
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
    callbacks : List[Callable[[Any], Any]]
        If set, pass a list of callables that will be called on the
        DICOM file after it is received and persisted to disk.
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
    server = StoreSCPServer(
        node, data_dir=data_dir, sort_by=sort_by, callbacks=callbacks
    )
    if block:
        server.run(block=True)
        return None

    server.run(block=False)
    return server
