# Moving DICOM data

Once you have [found](finding.md) the DICOM data you want, it is
time that you start moving it from the PACS to your machine.

!!! note
    Make sure that your DICOM node is declared on the DICOM network
    and that you are authorized to Q\R.

!!! note
    When performing C-MOVE operations, ensure that the port you
    are using (typically 104 or 11112) is open.


```python
from pacsanini.models import DicomNode
from pacsanini.net import move_studies

study_uids = ["Study1", "Study2", "Study3"]

local_node = DicomNode(aetitle="my_aetitle", ip="my.address", port=11112)
dest_node = local_node

called_node = DicomNode(aetitle="pacs_aetitle", ip="pacs.address", port=104)

dest_dir = "dicom_dir"

move_results = move_studies(
    local_node=local_node,
    called_node=called_node,
    dest_node=dest_node,
    study_uids=study_uids,
    directory=dest_dir,
)
for (status, uid) in move_results:
    print(status, uid)
```

In this example, we have declared our own DICOM node information (`local_node`),
the PACS node (`called_node`), and the DICOM node to send the DICOM data to (`dest_node`).

In addition, we have instructed that the DICOM data be persisted under the `dest_dir` directory.

When the `move_studies` function is running, a storescp server will be instantiated
and will enable the reception of the DICOM data.

The result of a call to the `move_studies` method is a generator that yields tuples
consisting of the C-MOVE's return code as an int and the corresponding UID.

If you are requesting large amounts of data that can take multiple days to obtain, you may want
to consider throttling your C-MOVE requests. This can be done by passing the `start_time` and
`end_time` parameters to the `move_studies` method. In the following example, C-MOVE requests
will only be made between `20:00` at night and `08:00` in the morning.

```python
move_results = move_studies(
    local_node=local_node,
    called_node=called_node,
    dest_node=dest_node,
    study_uids=study_uids,
    directory=dest_dir,
    start_time="20:00",
    end_time="08:00",
)
for (status, uid) in move_results:
    print(status, uid)
```
