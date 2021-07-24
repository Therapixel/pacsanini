# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The df_parser module provides methods for parsing DICOM files
using the base_parser module and return data frame instances.
"""
from os import PathLike
from typing import Union

import pandas as pd

from pacsanini.io.base_parser import parse_dir
from pacsanini.parse import DicomTagGroup


def _write_results(result: dict, results_list: list):
    results_list.append(result)


def parse_dir2df(
    src: Union[str, PathLike],
    parser: DicomTagGroup,
    nb_threads: int = 1,
    include_path: bool = True,
) -> pd.DataFrame:
    """Parse a DICOM directory and return the parsed DICOM
    tag results as a DataFrame.

    Parameters
    ----------
    src : Union[str, PathLike]
        The input file or DICOM directory to parse.
    parser : DicomTagGroup
        The DicomTagGroup instance specifying which DICOM
        tags to parse and how.
    nb_threads : int
        The number of threads to use when parsing DICOM
        files. The default is 1.
    include_path : bool
        If True, add a "dicom_path" key to the parsed results.
        The default is True.

    Returns
    -------
    pd.DataFrame
        The parsed DICOM tag results as a DataFrame.
    """
    results: list = []

    parse_dir(
        src,
        parser,
        _write_results,
        callback_args=(results,),
        nb_threads=nb_threads,
        include_path=include_path,
    )

    return pd.DataFrame(results)
