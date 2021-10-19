# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The parser module module provides convenience methods for parsing DICOM files
and storing results into a given database.
"""
from datetime import datetime

from pacsanini.db.crud import DBWrapper, add_image
from pacsanini.io.base_parser import parse_dir


def _inner_sql(result: dict, db_wrapper: DBWrapper, institution_name: str):
    dcm = result.pop("dicom")
    add_image(
        db_wrapper.conn(),
        dcm,
        institution=institution_name,
        filepath=result["dicom_path"],
    )


def parse_dir2sql(
    src: str,
    conn_uri: str,
    institution_name: str = None,
    nb_threads: int = 1,
    create_tables: bool = False,
):
    """Parse a DICOM directory and persist the found results in the database
    specified by the conn_uri parameter.

    Notes
    -----
    Unlike other parse_dir wrapper methods, this method does not use the DICOMTagParser
    instance. Parsed DICOM files will have basic DICOM tag metadata stored in traditional
    columns as well as the entire DICOM file (pixel data excluded) stored in JSON format.

    Parameters
    ----------
    src : str
        The DICOM directory to parse.
    conn_uri : str
        The database's connection URI to use.
    institution_name : str
        If specified, associate the parsed DICOM files with the name of an
        institution. If unset, this will default to unknwon followed by today's
        date in the YYYYMMDD format.
    nb_threads : int
        The number of threads to use. This defaults to 1.
    create_tables : bool
        If True, create the database tables before inserting the first
        parser result. The default is False.
    """
    if institution_name is None:
        institution_name = f"unknown_{datetime.now().strftime('%Y%m%d')}"

    with DBWrapper(conn_uri, create_tables=create_tables, debug=True) as wrapper:
        parse_dir(
            src,
            None,
            _inner_sql,
            nb_threads=nb_threads,
            callback_args=(wrapper, institution_name),
            include_path=True,
        )
