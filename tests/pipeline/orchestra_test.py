# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test the overall pacsanini pipeline."""
import os

import pytest

from pacsanini.config import PacsaniniConfig
from pacsanini.db import Images, utils
from pacsanini.pipeline import run_pacsanini_pipeline


@pytest.mark.pipeline
def test_run_pacsanini_pipeline(pacsanini_orthanc_config: str):
    """Test that the overall pacsanini pipeline works correctly."""
    run_pacsanini_pipeline(pacsanini_orthanc_config, init_db=True)

    config = PacsaniniConfig.from_yaml(pacsanini_orthanc_config)
    dcmdir = config.storage.directory
    assert os.path.exists(dcmdir)
    file_count = 0
    for _, _, files in os.walk(dcmdir):
        file_count += len([f for f in files])
    assert file_count > 1

    with utils.get_db_session(config.storage.resources) as db_session:
        db_images = db_session.query(Images).all()
        assert len(db_images)
        assert len(db_images) == file_count
