"""Test that resource files can correctly be read
if they have the good columns.
"""
import pandas as pd
import pytest

from pacsanini import utils
from pacsanini.errors import InvalidResourceFile
from pacsanini.models import QueryLevel


@pytest.mark.utils
def test_read_resources(tmpdir):
    """Test that resources can correctly be read."""
    patient_lvl_data = pd.DataFrame(
        {
            "PatientID": ["patient1", "patient2", "patient3"],
            "RandomCol": ["val1", "val2", "val3"],
        }
    )
    study_lvl_data = pd.DataFrame({"StudyInstanceUID": ["study1", "study2", "study3"]})

    pat_path = tmpdir.join("patients.csv")
    study_path = tmpdir.join("studies.csv")

    patient_lvl_data.to_csv(pat_path, index=False)
    study_lvl_data.to_csv(study_path, index=False)

    patients = utils.read_resources(pat_path, QueryLevel.PATIENT)
    assert patients == ["patient1", "patient2", "patient3"]

    studies = utils.read_resources(study_path, QueryLevel.STUDY)
    assert studies == ["study1", "study2", "study3"]

    with pytest.raises(InvalidResourceFile):
        utils.read_resources(pat_path, QueryLevel.STUDY)
