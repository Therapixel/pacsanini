# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Database utilities for managing/initializing the pacsanini database."""
import csv
import os

from contextlib import contextmanager
from time import time
from typing import Generator, List

from alembic import command
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy_utils import create_database, database_exists

from pacsanini.config import PacsaniniConfig
from pacsanini.db.migrate import get_alembic_config, get_latest_version
from pacsanini.db.models import Image, Patient, Series, Study, StudyFind


def initialize_database(
    config: PacsaniniConfig, echo: bool = True, force_init: bool = False
) -> None:
    """Initialize the pacsanini database after checking whether it
    already exists or not.

    Parameters
    ----------
    config : PacsaniniConfig
        The configuration to use for the database initialization.
    echo : bool
        Whether to echo SQL statements made during the creation
        of the database. The default is True.
    force_init : bool
        Force the database initialization regardless of whether it already exists.
        This is mainly useful for sqlite databases as the sqlite file will be created
        as soon as the engine is created. The default is False.
    """
    logger.info("Initializing new pacsanini database instance...")
    if not database_exists(config.storage.resources) or force_init:
        create_database(config.storage.resources)

        alembic_config = get_alembic_config(config)
        revision = get_latest_version(alembic_config)

        command.current(alembic_config)
        if echo:
            command.upgrade(alembic_config, revision, sql=True)
        command.upgrade(alembic_config, revision)
    else:
        logger.info("pacsanini database already found... Skipping initialization.")


@contextmanager
def get_db_session(db_uri: str) -> Generator[Session, None, None]:
    """Obtain a database session whose opening and closing is context
    managed. If an error is raised during the session's usage, the
    current transaction will be rolled back, closed, and the error will
    be raised. It is the caller's responsibility to commit transactions.

    Parameters
    ----------
    db_uri : str
        The database's URI.

    Returns
    -------
    Generator[Session, None, None]
        The context-wrapped Session instance.
    """
    engine: Engine = None
    db_session: Session = None
    try:
        if db_uri.lower().startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        else:
            connect_args = None
        engine = create_engine(db_uri, connect_args=connect_args)
        DBSession = sessionmaker(bind=engine)
        db_session = DBSession()
        yield db_session
    except:
        if db_session is not None:
            db_session.rollback()
        raise
    finally:
        if db_session is not None:
            db_session.close()
        if engine is not None:
            engine.dispose()


TABLES = {
    Patient.__tablename__: Patient,
    Study.__tablename__: Study,
    StudyFind.__tablename__: StudyFind,
    Series.__tablename__: Series,
    Image.__tablename__: Image,
}


def dump_database(
    session: Session, output: str = None, tables: List[str] = None
) -> None:
    """Dump the pacsanini database into CSV files. Each CSV file
    corresponds to a database table.

    Parameters
    ----------
    session : Session
        The database session to use for dumping data.
    output : str
        If set, write all output files under the specified directory.
        If it doesn't exist, it will be created. The default is the
        current directory.
    tables : List[str]
        Optional. If set, specify the tables to dump in CSV format.

    Raises
    ------
    ValueError
        A ValueError is raised if a table name in the tables parameter
        does not correspond to an existing table.
    """
    target_tables = list(TABLES.keys())
    if tables:
        for table_name in tables:
            if table_name not in TABLES:
                raise ValueError(
                    f'"{table_name}" does not exist in the pacsanini database.'
                )
        target_tables = tables

    if output:
        os.makedirs(output, exist_ok=True)
    else:
        output = os.getcwd()

    for table_name in target_tables:
        path = os.path.join(output, f"{table_name}.csv")

        table = TABLES[table_name]
        table_cols = [col.name for col in table.__mapper__.columns]  # type: ignore
        start_time = time()
        logger.info(f"Initiating dump of the {table_name} table...")

        with open(path, "w", newline="", encoding="utf-8") as out:
            writer = csv.DictWriter(out, table_cols)
            writer.writeheader()
            for record in session.query(table).all():
                writer.writerow({col: getattr(record, col) for col in table_cols})

        end_time = time()
        logger.info(
            f"Finished dump of the {table_name} table in {end_time-start_time:.3f}s"
        )
