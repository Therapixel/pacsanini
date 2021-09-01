# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""Test that parsing DICOM files works with a SQL backend."""
import os

from typing import List

import pytest

from pydicom import FileDataset
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pacsanini.db.models import Images
from pacsanini.db.parser import parse_dir2sql


@pytest.mark.db
def test_parse_sql2db(data_dir: str, sqlite_db_path: str, dicom: FileDataset):
    """Test that parsing DICOM data and persisting it into the
    database works well.
    """
    parse_dir2sql(data_dir, sqlite_db_path, institution_name="foobar")

    engine = create_engine(sqlite_db_path)
    Session = sessionmaker(bind=engine)
    session = Session()

    results: List[Images] = session.query(Images).all()
    assert len(results) > 1
    for result in results:
        assert os.path.exists(result.filepath)
        assert result.institution == "foobar"

    file_count = 0
    for _, _, files in os.walk(data_dir):
        file_count += len([f for f in files if f.endswith("dcm")])

    assert len(results) == file_count

    res: Images = (
        session.query(Images).filter(Images.image_uid == dicom.SOPInstanceUID).first()
    )
    assert res

    session.close()
    engine.dispose()
