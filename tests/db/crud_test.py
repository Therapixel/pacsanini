"""Test that CRUD methods function correctly."""
import pytest

from pydicom import FileDataset
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from pacsanini.db.crud import add_image
from pacsanini.db.models import Images


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
