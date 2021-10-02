# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that database commands run from the command line work correctly."""
import os

import pytest
import yaml

from click.testing import CliRunner

from pacsanini.cli.db import TABLES, dump_cli, init_cli
from pacsanini.config import PacsaniniConfig


@pytest.fixture
def pacsanini_config(tmpdir_factory):
    """Generate a temporary configuration where a new database will be created."""
    tmpdir = tmpdir_factory.mktemp("data")

    config_path = os.path.join(str(tmpdir), "pacsanini.yaml")
    data_dir = os.path.join(str(tmpdir), "dcmdir")
    sqlite_db = os.path.join(f"sqlite:///{str(tmpdir)}", "resources.db")

    config = PacsaniniConfig(storage={"resources": sqlite_db, "directory": data_dir})
    config_dict = config.dict()
    with open(config_path, "w") as out:
        yaml.safe_dump(config_dict, out)
    yield config_path


@pytest.mark.cli
def test_create_and_dump_database(tmpdir, pacsanini_config: str):
    """Test that the database can be created and dumped
    from the command line.
    """
    runner = CliRunner()

    result_init = runner.invoke(init_cli, ["-f", pacsanini_config])
    assert result_init.exit_code == 0

    result_dump = runner.invoke(dump_cli, ["-f", pacsanini_config, "-o", str(tmpdir)])
    assert result_dump.exit_code == 0
    for table_name in TABLES.keys():
        path = os.path.join(str(tmpdir), f"{table_name}.csv")
        assert os.path.exists(path)
