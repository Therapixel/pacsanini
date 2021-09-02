"""Test that CRUD methods function correctly."""
import pytest

from pydicom import FileDataset
from sqlalchemy.orm import Session

from pacsanini.db.crud import add_found_study, add_image
from pacsanini.db.models import Images, StudyFind


@pytest.mark.db
def test_add_image(dicom: FileDataset, sqlite_session: Session):
    """Test that adding an image to the database works well."""
    image1 = add_image(sqlite_session, dicom)
    assert isinstance(image1, Images)
    assert image1.image_uid == dicom.SOPInstanceUID

    assert len(sqlite_session.query(Images).all()) == 1

    image2 = add_image(sqlite_session, dicom)
    assert image2 is None

    assert len(sqlite_session.query(Images).all()) == 1


@pytest.mark.db
def test_add_found_study(dicom: FileDataset, sqlite_session: Session):
    """Test that adding a study finding (from a C-FIND request works
    well.
    """
    dcm_finding = dicom
    study_finding1 = add_found_study(sqlite_session, dcm_finding)
    assert isinstance(study_finding1, StudyFind)
    assert study_finding1.study_uid == dcm_finding.StudyInstanceUID

    assert len(sqlite_session.query(StudyFind).all()) == 1

    study_finding2 = add_found_study(sqlite_session, dcm_finding)
    assert study_finding2 is None

    assert len(sqlite_session.query(StudyFind).all()) == 1
