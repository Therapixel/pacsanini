# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test the c_echo module and make sure that results are correctly obtained."""
import pytest

from pynetdicom import AE, ALL_TRANSFER_SYNTAXES, evt
from pynetdicom.sop_class import VerificationSOPClass

from pacsanini.net.c_echo import echo


@pytest.fixture
def echoscp(test_dest_node: dict):
    """Simple echoscp server for testing purposes."""

    def handle_cecho(event):
        return 0x0000

    ae = AE(ae_title=test_dest_node["aetitle"].encode())
    ae.add_supported_context(VerificationSOPClass, ALL_TRANSFER_SYNTAXES)
    server = None
    try:
        server = ae.start_server(
            ("", test_dest_node["port"]),
            evt_handlers=[(evt.EVT_C_ECHO, handle_cecho)],
            block=False,
        )
        yield ae
    finally:
        if server is not None:
            server.shutdown()


@pytest.mark.net
def test_c_echo_invalid_node(test_src_node: dict):
    """Test that if the destination node does not have correct
    information, the c_echo methods returns an error.
    """
    with pytest.raises(ValueError):
        echo(test_src_node, test_src_node)


@pytest.mark.net
def test_c_echo_unreachable_node(test_src_node: dict):
    """Test that if the destination cannot be reached,
    a value of -1 is returned.
    """
    unreachable_node = test_src_node.copy()
    unreachable_node["ip"] = "www.localhost.com"
    unreachable_node["port"] = 11118

    result = echo(test_src_node, unreachable_node)
    assert result == -1


@pytest.mark.net
def test_c_echo(echoscp: AE, test_src_node: dict, test_dest_node: dict):
    """Test that sending a C-ECHO message to a functional
    DICOM node works correctly.
    """
    result = echo(test_src_node, test_dest_node)
    assert result == 0
