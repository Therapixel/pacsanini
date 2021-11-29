# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that database commands run from the command line work correctly."""
import os
import sqlite3 as sql

import pytest
import yaml

from click.testing import CliRunner
from py._path.local import LocalPath

from pacsanini.cli.db import TABLES, dump_cli, init_cli, upgrade_cli
from pacsanini.config import PacsaniniConfig


@pytest.fixture
def sqlite_db_url(tmpdir: LocalPath):
    """Return the URL for the sqlite database"""
    return os.path.join(tmpdir, "test.db")


@pytest.fixture
def pacsanini_config(tmpdir_factory, sqlite_db_url: str):
    """Generate a temporary configuration where a new database will be created."""
    tmpdir = tmpdir_factory.mktemp("data")

    config_path = os.path.join(str(tmpdir), "pacsanini.yaml")
    data_dir = os.path.join(str(tmpdir), "dcmdir")
    sqlite_db = f"sqlite:///{sqlite_db_url}"

    config = PacsaniniConfig(storage={"resources": sqlite_db, "directory": data_dir})
    config_dict = config.dict()
    with open(config_path, "w") as out:
        yaml.safe_dump(config_dict, out)
    yield config_path

    if os.path.exists(sqlite_db):
        os.remove(sqlite_db)


@pytest.mark.cli
@pytest.mark.db
def test_create_and_dump_database(tmpdir: LocalPath, pacsanini_config: str):
    """Test that the database can be created and dumped
    from the command line.
    """
    runner = CliRunner()

    result_init = runner.invoke(init_cli, ["-f", pacsanini_config])
    assert result_init.exit_code == 0

    result_dump = runner.invoke(dump_cli, ["-f", pacsanini_config, "-o", str(tmpdir)])
    assert result_dump.exit_code == 0
    for table_name in TABLES:
        path = os.path.join(str(tmpdir), f"{table_name}.csv")
        assert os.path.exists(path)


@pytest.mark.cli
@pytest.mark.db
def test_upgrade_database(pacsanini_config: str, sqlite_db_url: str):
    """Test that a database upgrade functions correctly."""
    runner = CliRunner()

    runner.invoke(init_cli, ["-f", pacsanini_config])
    result = runner.invoke(upgrade_cli, ["-f", pacsanini_config, "--dry-run"])
    assert result.exit_code == 0

    conn = sql.connect(sqlite_db_url)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE alembic_version;")
    conn.commit()
    cursor.close()
    conn.close()

    result = runner.invoke(upgrade_cli, ["-f", pacsanini_config, "--dry-run"])
    assert result.exit_code == 0

    result = runner.invoke(upgrade_cli, ["-f", pacsanini_config])
    conn = sql.connect(sqlite_db_url)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = [res[0] for res in cursor.fetchall()]
    assert "alembic_version" in table_names
    cursor.close()
    conn.close()
