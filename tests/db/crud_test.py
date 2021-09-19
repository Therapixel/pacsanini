"""Test that CRUD methods function correctly."""
from datetime import datetime, timedelta
from typing import Tuple

import pytest

from pydicom import FileDataset
from sqlalchemy.orm import Session

from pacsanini.db import crud
from pacsanini.db.models import Images, StudyFind


@pytest.fixture
def add_studies_to_find(sqlite_session: Session):
    """Add studies in the database that need to be found."""
    study1 = StudyFind(
        patient_name="patient1",
        study_uid="study1",
        study_date=datetime.now(),
        accession_number="accession1",
    )
    study2 = StudyFind(
        patient_name="patient1",
        study_uid="study2",
        study_date=datetime.now(),
        accession_number="accession2",
        found_on=datetime.utcnow(),
        retrieved_on=datetime.utcnow(),
    )

    sqlite_session.add(study1)
    sqlite_session.add(study2)
    sqlite_session.commit()

    yield study1, study2

    sqlite_session.delete(study1)
    sqlite_session.delete(study2)
    sqlite_session.commit()


@pytest.mark.db
def test_add_image(dicom: FileDataset, sqlite_session: Session):
    """Test that adding an image to the database works well."""
    image1 = crud.add_image(sqlite_session, dicom)
    assert isinstance(image1, Images)
    assert image1.image_uid == dicom.SOPInstanceUID

    assert len(sqlite_session.query(Images).all()) == 1

    image2 = crud.add_image(sqlite_session, dicom)
    assert image2 is None

    assert len(sqlite_session.query(Images).all()) == 1


@pytest.mark.db
def test_add_found_study(dicom: FileDataset, sqlite_session: Session):
    """Test that adding a study finding (from a C-FIND request works
    well.
    """
    dcm_finding = dicom
    study_finding1 = crud.add_found_study(sqlite_session, dcm_finding)
    assert isinstance(study_finding1, StudyFind)
    assert study_finding1.study_uid == dcm_finding.StudyInstanceUID

    assert len(sqlite_session.query(StudyFind).all()) == 1

    study_finding2 = crud.add_found_study(sqlite_session, dcm_finding)
    assert study_finding2 is None

    assert len(sqlite_session.query(StudyFind).all()) == 1


@pytest.mark.db
def test_update_study(
    add_studies_to_find: Tuple[StudyFind, StudyFind], sqlite_session: Session
):
    """Test that studies in the studies_find table are correctly updated."""
    _, study_to_update = add_studies_to_find

    before = datetime.utcnow()
    updated_study = crud.update_retrieved_study(
        sqlite_session, study_to_update.study_uid
    )

    assert updated_study is not None and isinstance(updated_study, StudyFind)
    assert updated_study.study_uid == study_to_update.study_uid
    assert (
        before - timedelta(seconds=1)
        < updated_study.retrieved_on
        < before + timedelta(seconds=1)
    )


@pytest.mark.db
def test_get_studies_to_retrieve(
    add_studies_to_find: Tuple[StudyFind, StudyFind], sqlite_session: Session
):
    """Test that only studies that have not yet been retrieved are
    returned.
    """
    studies_to_find = crud.get_studies_to_move(sqlite_session)
    assert len(studies_to_find) == 1

    expected_study, _ = add_studies_to_find
    found_study = studies_to_find[0]
    assert found_study.study_uid == expected_study.study_uid

    study_uids_to_find = crud.get_study_uids_to_move(sqlite_session)
    assert len(studies_to_find) == 1
    assert study_uids_to_find[0] == expected_study.study_uid
