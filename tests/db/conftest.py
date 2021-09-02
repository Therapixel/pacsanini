# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Declare fixtures for the db testing module."""
import os

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from pacsanini.db.utils import initialize_database


@pytest.fixture()
def sqlite_db_path(tmpdir: str) -> str:
    """A temp path for the sqlite database."""
    path = os.path.join(str(tmpdir), "test.db")
    db_path = f"sqlite:///{path}"
    engine = None
    try:
        engine = create_engine(db_path)
        initialize_database(engine, echo=False, force_init=True)
    finally:
        engine.dispose()

    yield db_path

    if os.path.exists(path):
        os.remove(path)


@pytest.fixture()
def sqlite_session(sqlite_db_path: str) -> Session:
    """Return a session for the sqlite datatabase."""
    engine = create_engine(sqlite_db_path)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    yield session

    session.close()
    engine.dispose()
