# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Simple utilities to facilitate the ingestion of resource values
into the application.
"""
from typing import List

import pandas as pd

from pacsanini.errors import InvalidResourceFile
from pacsanini.models import QueryLevel


def read_resources(resources_path: str, query_level: QueryLevel) -> List[str]:
    """Read a list of DICOM resources.

    Parameters
    ----------
    resources_path : str
        The file path of the DICOM resources file to read.
    query_level : QueryLevel
        A way of indicating which field to read in the file. If PATIENT,
        the PatientID column will be read. If STUDY, the StudyInstanceUID
        column will be read.

    Returns
    -------
    List[str]
        A list of unique UIDS found in the given file.
    """
    resources = pd.read_csv(resources_path)
    if resources.shape[1] == 1:
        resources = resources[resources.columns[0]].unique().tolist()
    else:
        if QueryLevel.PATIENT == query_level:
            if not "PatientID" in resources.columns:
                raise InvalidResourceFile(
                    f"Expected to find a column named PatientID in {resources_path}"
                )
            resources = resources["PatientID"].unique().tolist()
        else:
            if not "StudyInstanceUID" in resources.columns:
                raise InvalidResourceFile(
                    f"Expected to find a column named StudyInstaceUID in {resources_path}"
                )
            resources = resources["StudyInstanceUID"].unique().tolist()

    return resources
