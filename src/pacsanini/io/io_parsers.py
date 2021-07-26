# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The io_parsers provides generic extensions of the base_parser
module methods that can be called and conveniently used by users.
"""
import csv
import json

from datetime import datetime
from os import PathLike
from typing import TextIO, Union

from pacsanini.io.base_parser import parse_dir
from pacsanini.parse import DicomTagGroup


def _write_results(result: dict, reader: csv.DictWriter):
    reader.writerow(result)


def parse_dir2csv(
    src: Union[str, PathLike],
    parser: DicomTagGroup,
    dest: Union[str, PathLike, TextIO],
    nb_threads: int = 1,
    include_path: bool = True,
    mode: str = "w",
):
    """Parse a DICOM directory and write results to a CSV
    file.

    Parameters
    ----------
    src : Union[str, PathLike]
        The DICOM file or directory to parse.
    parser : DicomTagGroup
        The DicomTagGroup instance specifying which DICOM
        tags to parse and how.
    dest : Union[str, PathLike, TextIO]
        The destination path to write the results to.
    nb_threads : int
        The number of threads to use when parsing DICOM
        files. The default is 1.
    include_path : bool
        If True, add a "dicom_path" key to the parsed results.
        The default is True.
    mode : str
        Whether to write ("w") or append ("a") to the
        destination file.
    """
    fieldnames = [tag.tag_alias for tag in parser.tags]
    if include_path:
        fieldnames.append("dicom_path")

    if isinstance(dest, (str, PathLike)):
        with open(dest, mode, newline="") as output:
            reader = csv.DictWriter(output, fieldnames=fieldnames)
            if mode == "w":
                reader.writeheader()

            parse_dir(
                src,
                parser,
                _write_results,
                callback_args=(reader,),
                nb_threads=nb_threads,
                include_path=include_path,
            )
    else:
        reader = csv.DictWriter(dest, fieldnames=fieldnames)
        if mode == "w":
            reader.writeheader()

        parse_dir(
            src,
            parser,
            _write_results,
            callback_args=(reader,),
            nb_threads=nb_threads,
            include_path=include_path,
        )


def _append_results(result: dict, *, results_list: list):
    results_list.append(result)


def _json_serializer(value):
    if isinstance(value, datetime):
        # Format datetime the same way that csv writers do.
        return value.isoformat(sep=" ")
    return value


def parse_dir2json(
    src: Union[str, PathLike],
    parser: DicomTagGroup,
    dest: Union[str, PathLike, TextIO],
    nb_threads: int = 1,
    include_path: bool = True,
    mode: str = "w",
):
    """Parse a DICOM directory and write results to a JSON
    file.

    Parameters
    ----------
    src : Union[str, PathLike]
        The DICOM file or directory to parse.
    parser : DicomTagGroup
        The DicomTagGroup instance specifying which DICOM
        tags to parse and how.
    dest : Union[str, PathLike, TextIO]
        The destination path to write the results to.
    nb_threads : int
        The number of threads to use when parsing DICOM
        files. The default is 1.
    include_path : bool
        If True, add a "dicom_path" key to the parsed results.
        The default is True.
    mode : str
        Whether to write ("w") or append ("a") to the
        destination file.
    """
    fieldnames = [tag.tag_alias for tag in parser.tags]
    if include_path:
        fieldnames.append("dicom_path")

    results: list = []
    parse_dir(
        src,
        parser,
        _append_results,
        callback_kwargs={"results_list": results},
        nb_threads=nb_threads,
        include_path=include_path,
    )

    if isinstance(dest, (str, PathLike)):
        if mode == "a":
            mode = "r+"
        with open(dest, mode) as output:
            if mode == "r+":
                old_results = json.load(output.read())
                results += old_results["dicom_tags"]
            json.dump(
                {"dicom_tags": results}, output, indent=2, default=_json_serializer
            )
    else:
        json.dump({"dicom_tags": results}, dest, indent=2, default=_json_serializer)
