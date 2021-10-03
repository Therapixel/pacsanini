# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The c_store module exposes methods that can be used to send DICOM
from a local node to a destination node over a C-STORE connection.
"""
import os

from typing import Generator, Union

from pydicom import Dataset, dcmread
from pydicom.errors import InvalidDicomError
from pydicom.uid import (
    DeflatedExplicitVRLittleEndian,
    ExplicitVRBigEndian,
    ExplicitVRLittleEndian,
    ImplicitVRLittleEndian,
)
from pynetdicom import AE
from pynetdicom.presentation import StoragePresentationContexts

from pacsanini.models import DicomNode


def send_dicom(
    dcm_path: str,
    *,
    src_node: Union[DicomNode, dict],
    dest_node: Union[DicomNode, dict],
) -> Generator[Dataset, None, None]:
    """Send one or multiple DICOM files from the source node
    to the dest node. If the dcm_path is a directory, non-DICOM
    files will be ignored.

    Parameters
    ----------
    dcm_path : str
        The path to the DICOM file to send or the DICOM directory
        (in which case DICOM files will be collected recursively).
    src_node : Union[DicomNode, dict]
        The source DICOM node to use for sending the DICOM data.
    dest_node : Union[DicomNode, dict]
        The destination DICOM node to send the DICOM data to.

    Yields
    ------
    Generator[Dataset, None, None]
        The status of the C-STORE requests as Dataset instances.
    """
    if isinstance(src_node, dict):
        src_node = DicomNode(**src_node)
    if isinstance(dest_node, dict):
        dest_node = DicomNode(**dest_node)

    if os.path.isfile(dcm_path):
        dcm_files = [dcm_path]
    else:
        dcm_files = []
        append = dcm_files.append
        for root, _, files in os.walk(dcm_path):
            for fname in files:
                append(os.path.join(root, fname))

    ae = AE(ae_title=src_node.aetitle)
    transfer_syntax = [
        ExplicitVRLittleEndian,
        ImplicitVRLittleEndian,
        DeflatedExplicitVRLittleEndian,
        ExplicitVRBigEndian,
    ]
    for ctx in StoragePresentationContexts:
        ae.add_requested_context(ctx.abstract_syntax, transfer_syntax)

    assoc = ae.associate(dest_node.ip, dest_node.port, ae_title=dest_node.aetitle)
    if assoc.is_established:
        for path in dcm_files:
            try:
                dcm = dcmread(path)
                yield assoc.send_c_store(dcm)
            except InvalidDicomError:
                pass
    assoc.release()
