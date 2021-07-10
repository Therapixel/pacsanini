# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The echo module provides methods for checking if associations
can be made between two DICOM nodes.
"""
from typing import Union

from pynetdicom import AE

from pacsanini.models import DicomNode


def echo(
    local_node: Union[dict, DicomNode], called_node: Union[dict, DicomNode]
) -> int:
    """Check that the DICOM connection is OK between two nodes
    using C-ECHO.

    Parameters
    ----------
    local_node : Union[dict, DicomNode]
        The source/local node that you want to test the connection
        from.
    called_node : Union[dict, DicomNode]
        The target node that you want to check your connection with.

    Returns
    -------
    int
        An integer corresponding to the status code of the established
        connection. 0 means the association was successfull. -1 means
        that the connection could not be established.

    Raises
    ------
    ValueError
        An error is raised if the called_node does not have its ip
        and port attributes set.
    """
    if isinstance(local_node, dict):
        local_node = DicomNode(**local_node)
    if isinstance(called_node, dict):
        called_node = DicomNode(**called_node)

    if not called_node.has_net_info:
        raise ValueError(f"{called_node} does not have a network address.")

    ae = AE(ae_title=local_node.aetitle)
    ae.add_requested_context("1.2.840.10008.1.1")

    association = ae.associate(called_node.ip, called_node.port)
    status = -1
    if association.is_established:
        status_ds = association.send_c_echo()
        status = status_ds.Status
        association.release()

    return status
