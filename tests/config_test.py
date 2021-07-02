# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that the configuration elements of the pacsanini application
can be manipulated with in an expected manner.
"""
from datetime import datetime, time
from unittest.mock import patch

import pytest

from pydantic import ValidationError

from pacsanini import config


@pytest.mark.config
def test_move_config_valid_times():
    """Test that time parsing for the end and start time functions
    correctly.
    """
    move_config = config.MoveConfig()
    assert move_config.start_time is None
    assert move_config.end_time is None

    move_config = config.MoveConfig(start_time="", end_time="")
    assert move_config.start_time is None
    assert move_config.end_time is None

    move_config = config.MoveConfig(start_time=time(hour=20), end_time=time(hour=20))
    assert move_config.start_time is None
    assert move_config.end_time is None

    move_config = config.MoveConfig(
        start_time=time(hour=20, minute=10), end_time="12:02:34"
    )
    assert move_config.start_time == time(hour=20, minute=10)
    assert move_config.end_time == time(hour=12, minute=2, second=34)


@pytest.mark.config
def test_move_config_invalid_times():
    """Test that time parsing for the end and start time functions
    correctly.
    """
    invalid_configs = [
        {"start_time": time(hour=20), "end_time": None},
        {"start_time": "", "end_time": time(hour=20)},
        {"start_time": "3", "end_time": time(hour=12)},
    ]

    for cfg in invalid_configs:
        with pytest.raises(ValueError):
            config.MoveConfig(**cfg)


@pytest.mark.config
def test_move_can_query():
    """Test that the move configuration can properly indicate
    whether queries can be made or not.
    """
    move_config = config.MoveConfig(start_time="", end_time=None)
    assert move_config.can_query()

    ref_time = time(20, 0, 1)
    move_config = config.MoveConfig(start_time=ref_time, end_time=ref_time)
    assert move_config.can_query()

    reference_dt = datetime(2021, 8, 1, 16)  # 2021-08-01 16:00:00
    with patch("pacsanini.config.MoveConfig.now", return_value=reference_dt):
        move_config = config.MoveConfig(
            start_time=time(8, 0, 0), end_time=time(17, 0, 0)
        )
        assert move_config.can_query()

        move_config = config.MoveConfig(
            start_time=time(16, 0, 0), end_time=time(17, 0, 0)
        )
        assert not move_config.can_query()

        move_config = config.MoveConfig(start_time=time(20), end_time=time(15))
        assert not move_config.can_query()

        move_config = config.MoveConfig(start_time=time(20), end_time=time(17))
        assert move_config.can_query()


@pytest.mark.config
def test_move_now():
    """Test that the now method yields the expected result."""
    move_config = config.MoveConfig()
    before = datetime.now()
    now = move_config.now()
    after = datetime.now()
    assert isinstance(now, datetime)
    assert before <= now <= after


@pytest.mark.config
def test_net_config():
    """Test that the net configuration is coherent."""
    net_template = {
        "local_node": {"ip": "", "port": "", "aetitle": "foobar"},
        "called_node": {"ip": "127.0.0.1", "port": "104", "aetitle": "foobar2"},
    }

    netconfig = config.NetConfig(**net_template)
    assert netconfig.local_node == netconfig.dest_node

    assert netconfig.local_node.ip is None
    assert netconfig.local_node.port is None
    assert netconfig.local_node.aetitle == b"foobar"

    assert netconfig.called_node.ip == "127.0.0.1"
    assert netconfig.called_node.port == 104
    assert netconfig.called_node.aetitle == b"foobar2"

    net_template["dest_node"] = {"ip": "", "port": "", "aetitle": "foobar3"}
    netconfig = config.NetConfig(**net_template)
    assert netconfig.local_node != netconfig.dest_node

    assert netconfig.dest_node.ip is None
    assert netconfig.dest_node.port is None
    assert netconfig.dest_node.aetitle == b"foobar3"

    net_template["called_node"]["port"] = None
    with pytest.raises(ValidationError):
        config.NetConfig(**net_template)


@pytest.mark.config
def test_pacsanini_config():
    """Test that the overall application configuration
    works as excepted.
    """
    now = datetime.now()
    config_dict = {
        "net": {
            "local_node": {"ip": "", "port": "", "aetitle": "foobar"},
            "called_node": {"ip": "127.0.0.1", "port": "104", "aetitle": "foobar2"},
        },
        "find": {"query_level": "PATIENT", "search_fields": [], "start_date": now},
    }

    pacsanini_config = config.PacsaniniConfig(**config_dict)
    assert pacsanini_config.can_find()
    assert pacsanini_config.get_tags() is None
