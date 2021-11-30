# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test the c_echo module and make sure that results are correctly obtained."""
import pytest

from pacsanini.config import PacsaniniConfig
from pacsanini.net.c_echo import echo


@pytest.mark.net
def test_c_echo_invalid_node(config: PacsaniniConfig):
    """Test that if the destination node does not have correct
    information, the c_echo methods returns an error.
    """
    test_src_node = config.net.local_node.dict()
    del test_src_node["ip"]
    with pytest.raises(ValueError):
        echo(test_src_node, test_src_node)


@pytest.mark.net
def test_c_echo_unreachable_node(config: PacsaniniConfig):
    """Test that if the destination cannot be reached,
    a value of -1 is returned.
    """
    unreachable_node = config.net.local_node.dict()
    unreachable_node["ip"] = "www.localhost.com"
    unreachable_node["port"] = 11118

    result = echo(config.net.local_node, unreachable_node)
    assert result == -1


@pytest.mark.net
def test_c_echo(config: PacsaniniConfig):
    """Test that sending a C-ECHO message to a functional
    DICOM node works correctly.
    """
    result = echo(config.net.local_node, config.net.called_node)
    assert result == 0
