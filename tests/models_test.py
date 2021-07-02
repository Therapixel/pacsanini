# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that net models can provide expected results and
contain expected attributes.
"""
import pytest

from pacsanini.models import DicomNode


@pytest.mark.net
def test_dicom_node_model():
    """Test that the DicomNode model provides
    expected behavior.
    """
    node1 = DicomNode(**{"aetitle": "foo", "ip": "localhost", "port": 11112})
    node2 = DicomNode(**{"aetitle": b"foo", "ip": "localhost", "port": "11112"})

    assert node1 == node2
    assert node1.has_net_info
    assert node2.has_net_info

    node3 = DicomNode(aetitle="foo")
    assert not node3.has_net_info

    invalid_nodes = [
        {},
        {"aetitle": 111112, "ip": "localhost", "port": 11112},
        {"aetitle": "foo", "ip": "localhost", "port": "11112.21"},
    ]
    for node in invalid_nodes:
        with pytest.raises(ValueError):
            DicomNode(**node)
