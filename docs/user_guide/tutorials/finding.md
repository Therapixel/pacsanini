# Finding DICOM data

At the beginning of every data collection process comes the question: how do I get the data?
For DICOM data, the answer usually is: from a PACS.
When you don't already know the identifiers of the data you want, you will have to prepare a
series of queries to obtain from the PACS the said data.

!!! note
    This tutorial assumes that you have access to communicate with your
    target PACS. If not, you can ask your administrator to grant access
    to you.

Data can be queried from PACSs with `pacsanini` using the *PATIENT* or *STUDY* information models.

To do so, you can run the following code snippet (you will need to adapt it slightly with the appropriate networking values):

```python
from datetime import datetime

from pacsanini.models import DicomNode
from pacsanini.net import study_find

# Declare a variable that represents your DICOM node.
local_node = DicomNode(aetitle="my_aetitle")
# Declare a variable that represents the PACS node.
called_node = DicomNode(aetitle="pacs_aetitle", ip="the.pacs.address", port=104)

# Declare the additional attributes you want to obtain
# from each C-FIND request.
# This is optional
dicom_fields = ["StudyInstanceUID", "PatientID"]

# Declare the date at which you want to start querying the PACS at.
start_date = datetime(year=2020, month=1, day=1)

# Without setting a end_date variable, the query will
# only be made for the start_date.
# To query over multiple dates, set an end_date.
end_date = datetime(year=2021, month=12, day=31)

# Specify a modality to emit requests for and limit results.
modality = "MG"

find_results = study_find(
    local_node,
    called_node,
    dicom_fields=dicom_fields,
    start_date=start_date,
    end_date=end_date,
    modality=modality,
)
for result in find_results:
    print(result.StudyInstanceUID)
```

The value returned by `study_find` will be a generator object yielding `pydicom.Dataset` instances.

If you want to perform queries using the *PATIENT* information model, simply use the `pacsanini.net.patient_find` method.
