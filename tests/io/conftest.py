# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Declare fixtures specific to the io module test suite."""
import os

import pytest

from pacsanini.parse import DicomTagGroup


@pytest.fixture(scope="module")
def tag_group(data_dir):
    """Return a DicomTagGroup instance using the pre-prepared
    DICOM tags configuration test file.
    """
    yaml_conf = os.path.join(data_dir, "tags_conf.json")
    return DicomTagGroup.from_json(yaml_conf)
