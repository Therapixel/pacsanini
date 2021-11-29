# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that the utility methods for the database work as excepted."""
import os

from datetime import datetime

import pytest

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pacsanini.config import PacsaniniConfig, StorageConfig
from pacsanini.db import models, utils, views


@pytest.fixture
def pristine_db_engine(tmpdir):
    """Return an engine connected to a pristine database."""
    sqlite_path = os.path.join(str(tmpdir), "dummy.db")
    engine = None
    try:
        engine = create_engine(f"sqlite:///{sqlite_path}")
        yield engine
    finally:
        if engine:
            engine.dispose()
        if os.path.exists(sqlite_path):
            os.remove(sqlite_path)


@pytest.fixture
def initialized_db_url(pristine_db_engine):
    """Return the URL of an initialized database."""
    config = PacsaniniConfig(
        storage=StorageConfig(resources=str(pristine_db_engine.url), directory="./")
    )
    utils.initialize_database(config)
    db_url = str(pristine_db_engine.url)
    return db_url


@pytest.mark.db
def test_get_db_session(initialized_db_url):
    """Test that getting a database session normally works well."""
    with utils.get_db_session(initialized_db_url) as db:
        assert isinstance(db, Session)


@pytest.mark.db
def test_get_db_session_with_exception(initialized_db_url):
    """Test that a database session that incurs an exception properly rolls back."""
    patient = models.Patient(
        patient_id="patient1",
        patient_name="patient1",
        patient_birth_date=datetime.utcnow(),
        institution="foobar",
    )
    with pytest.raises(Exception):
        with utils.get_db_session(initialized_db_url) as db:
            db.add(patient)
            raise Exception()

    with utils.get_db_session(initialized_db_url) as db:
        result = db.query(models.Patient).all()
        assert not result


@pytest.mark.db
def test_initialize_database(pristine_db_engine: Engine):
    """Test that the database can be correctly initialized and that the
    expected tables and views exist.
    """
    config = PacsaniniConfig(
        storage=StorageConfig(resources=str(pristine_db_engine.url), directory="./")
    )
    utils.initialize_database(config, echo=False)
    inspector = inspect(pristine_db_engine)

    expected_table_names = [
        "alembic_version",
        models.Image.__tablename__,
        models.Series.__tablename__,
        models.Study.__tablename__,
        models.StudyFind.__tablename__,
        models.Patient.__tablename__,
    ]
    assert set(inspector.get_table_names()) == set(expected_table_names)

    expected_view_names = [
        views.StudyMetaView.__tablename__,
        views.ManufacturerView.__tablename__,
    ]
    assert set(inspector.get_view_names()) == set(expected_view_names)
