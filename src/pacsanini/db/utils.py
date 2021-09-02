# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Database utilities for managing/initializing the pacsanini database."""
from loguru import logger
from sqlalchemy.engine import Engine
from sqlalchemy_utils import create_database, database_exists

from pacsanini.db.models import Base


def initialize_database(
    engine: Engine, echo: bool = True, force_init: bool = False
) -> None:
    """Initialize the pacsanini database after checking whether it
    already exists or not.

    Parameters
    ----------
    engine : Engine
        The connection engine to use for creating the database.
    echo : bool
        Whether to echo SQL statements made during the creation
        of the database. The default is True.
    force_init : bool
        Force the database initialization regardless of whether it already exists.
        This is mainly useful for sqlite databases as the sqlite file will be created
        as soon as the engine is created. The default is False.
    """
    logger.info(f"Initializing new pacsanini database instance {engine.url} ...")
    if not database_exists(engine.url) or force_init:
        orig_echo = engine.echo or False
        engine.echo = echo
        create_database(engine.url)
        Base.metadata.create_all(bind=engine)
        logger.info("pacsanini database initialized!")
        engine.echo = orig_echo
    else:
        logger.info("pacsanini database already found... Skipping initialization.")
