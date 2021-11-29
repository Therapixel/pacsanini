# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Custom commands used to enhance alembic capabilities. This defines methods
to check alembic versions in given databases and methods to create/drop views.
The migration methods were taken from:
https://alembic.sqlalchemy.org/en/latest/cookbook.html#create-operations-for-the-target-objects
"""
from pathlib import Path

from alembic import command, op
from alembic.config import Config
from alembic.operations import MigrateOperation, Operations
from sqlalchemy import create_engine, engine_from_config, inspect

from pacsanini.config import PacsaniniConfig


def get_alembic_config(config: PacsaniniConfig) -> Config:
    """Get an alembic configuration object that is initialized with
    the current generic settings to run.

    Parameters
    ----------
    config : PacsaniniConfig
        The pacsanini configuration object to use to obtain the
        database URL.

    Returns
    -------
    Config
        The alembic configuration object for applying migrations.
    """
    currentdir = Path(__file__).absolute().parent
    migrationsdir = currentdir.joinpath("migrations")
    config_file = str(migrationsdir.joinpath("alembic.ini"))

    alembic_config = Config(config_file)
    alembic_config.set_section_option("alembic", "here", str(currentdir))
    alembic_config.set_section_option("alembic", "script_location", str(migrationsdir))
    alembic_config.set_section_option(
        "alembic", "sqlalchemy.url", config.storage.resources
    )
    alembic_config.attributes["configure_logger"] = False
    return alembic_config


def get_latest_version(config: Config) -> str:
    """Get the latest migration version for the database from the project's
    configuration settings.
    """
    revision = ""

    def print_stdout(text: str, *args):
        nonlocal revision
        revision = text.split(" ")[0]

    config.print_stdout = print_stdout  # type: ignore
    command.current(config)
    return revision


def get_current_version(config: Config) -> str:
    """Get the database's current version from the database. If no revision
    was found, return an empty string.
    """
    url = config.get_main_option("sqlalchemy.url")
    engine = create_engine(url)
    version = ""
    try:
        if not inspect(engine).has_table("alembic_version"):
            return ""

        with engine.connect() as conn:
            results = conn.execute("SELECT version_num FROM alembic_version LIMIT 1;")
            for res in results:
                version = res[0]
                break
    finally:
        engine.dispose()
    return version


def table_exists(table: str, schema: str = None) -> bool:
    """Check whether a given table exists in the database and return True if
    it does -False otherwise.
    """
    config: Config = op.get_context().config
    engine = engine_from_config(
        config.get_section(config.config_ini_section), prefix="sqlalchemy."
    )
    return inspect(engine).has_table(table, schema=schema)


class ReplaceableObject:
    """The ReplaceableObject class is a simple wrapper class for
    storing view metadata so that they can be migrated with regular
    tables.
    """

    def __init__(self, name: str, sqltext: str):
        self.name = name
        self.sqltext = sqltext

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return self.name


class ReversibleOp(MigrateOperation):
    """The ReversibleOp class provides custom logic for migrating
    SQL views.
    """

    def __init__(self, target: ReplaceableObject):
        self.target = target

    @classmethod
    def _get_object_from_version(cls, operations: Operations, ident: str):
        version, objname = ident.split(".")
        module = operations.get_context().script.get_revision(version).module
        obj = getattr(module, objname)
        return obj

    @classmethod
    def invoke_for_target(cls, operations: Operations, target: ReplaceableObject):
        reverse_op = cls(target)
        return operations.invoke(reverse_op)

    @classmethod
    def replace(
        cls,
        operations: Operations,
        target: ReplaceableObject,
        replaces: str = None,
        replace_with: str = None,
    ):
        if replaces:
            old_obj = cls._get_object_from_version(operations, replaces)
            drop_old = cls(old_obj).reverse()
            create_new = cls(target)
        elif replace_with:
            old_obj = cls._get_object_from_version(operations, replace_with)
            drop_old = cls(target).reverse()
            create_new = cls(old_obj)
        else:
            raise TypeError("replaces or replace_with is required")

        operations.invoke(drop_old)
        operations.invoke(create_new)

    def reverse(self):
        raise NotImplementedError()


@Operations.register_operation("create_view", "invoke_for_target")
@Operations.register_operation("replace_view", "replace")
class CreateViewOp(ReversibleOp):
    """Implement an operation allowing for view creation."""

    def reverse(self):
        return DropViewOp(self.target)


@Operations.register_operation("drop_view", "invoke_for_target")
class DropViewOp(ReversibleOp):
    """Implement an operation allowing for view dropping."""

    def reverse(self):
        return CreateViewOp(self.target)


@Operations.implementation_for(CreateViewOp)
def create_view(operations: Operations, operation: ReversibleOp):
    """Custom command used to create views during migration operations."""
    operations.execute(  # type: ignore
        "CREATE VIEW %s AS %s"
        % (
            operation.target.name,
            operation.target.sqltext,
        )  # pylint: disable=consider-using-f-string
    )


@Operations.implementation_for(DropViewOp)
def drop_view(operations: Operations, operation: ReversibleOp):
    """Custom command used to drop views during migrations operations."""
    operations.execute(  # type: ignore
        "DROP VIEW %s" % operation.target.name
    )  # pylint: disable=consider-using-f-string
