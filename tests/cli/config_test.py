# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that the config functionalities of the pacsanini package can be
correctly accessed from the command line.
"""
import json
import os

import pytest
import yaml

from click.testing import CliRunner

from pacsanini.cli.config import config_cli
from pacsanini.config import PacsaniniConfig


@pytest.mark.cli
def test_config_stdout():
    """Test that the config generation works when outputing to stdout."""
    runner = CliRunner()

    result_yaml = runner.invoke(config_cli, ["--fmt", "yaml"])
    assert result_yaml.exit_code == 0
    assert result_yaml.output

    result_json = runner.invoke(config_cli, ["--fmt", "json"])
    assert result_json.exit_code == 0
    assert result_json.output

    yaml_conf_dict = yaml.safe_load(result_yaml.output)
    assert PacsaniniConfig(**yaml_conf_dict)

    json_conf_dict = json.loads(result_json.output)
    assert PacsaniniConfig(**json_conf_dict)


@pytest.mark.cli
def test_config_file(tmpdir):
    """Test that the parsing commands functions correctly."""
    runner = CliRunner()

    yaml_path = os.path.join(tmpdir, "conf.yaml")
    result_yaml = runner.invoke(config_cli, [yaml_path, "--fmt", "yaml"])
    assert result_yaml.exit_code == 0
    assert os.path.exists(yaml_path)

    json_path = os.path.join(tmpdir, "conf.json")
    result_json = runner.invoke(config_cli, [json_path, "--fmt", "json"])
    assert result_json.exit_code == 0
    assert os.path.exists(json_path)

    with open(yaml_path) as in_:
        yaml_conf_dict = yaml.safe_load(in_)
        assert PacsaniniConfig(**yaml_conf_dict)

    with open(json_path) as in_:
        json_conf_dict = json.load(in_)
        assert PacsaniniConfig(**json_conf_dict)
