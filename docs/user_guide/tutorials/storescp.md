# Storing DICOM data

In some cases, you way want to simply receive DICOM data from a third-party.
In such a case, you will want to use the `StoreSCPServer` class. Such a server
will handle C-STORE requests, which are used to transfer DICOM data.

## Running the server in blocking mode

```python
from pacsanini.net import StoreSCPServer

my_node_info = {"aetitle": "my_aetitle", "port": 11112}
dicom_dir = "/my/dicom/directory"

server = StoreSCPServer(my_node_info, data_dir=dicom_dir)

server.run(block=True)
```

The above example will start a `StoreSCPServer` on port 11112.

Stored files will be persisted under the provided `dicom_dir` (this defaults to the current directory).
An optional `sort_by` keyword argument can be passed to the `StoreSCPServer` to establish how the server will organize persisted data. This defaults to `pacsanini.models.StorageSortKey.PATIENT` (files will be stored as *PatientID*/*StudyInstanceUID*/*SeriesInstanceUID*/*SOPInstanceUID*.dcm). Other options are `StorageSortKey.STUDY`, `StorageSortKey.SERIES`,
and `StorageSortKey.IMAGE`.

Note that the above code is blocking. To stop the server from running, you will need to send a `KeyboardInterrupt` signal.

## Running the server in non-blocking mode

If you want the server to be active without blocking your current code execution, set the `block` value of the `StoreSCPServer.run` method to False (the default).

You can also use the `StoreSCPServer` instances inside context managers. In doing so, the context manager will return the given server instance and start the server in non-blocking mode. On exit, the server will automatically be shutdown.

```python
with StoreSCPServer(my_node_info, data_dir=dicom_dir) as server:
    # do stuff
```

## Passing callbacks to the server.

You may also pass callback methods to the `StoreSCPServer`. These methods will be executed after the successfull reception of each DICOM file and its persistence to disk.
Callback functions must be ready to accept the DICOM file in question (a `pydicom.Dataset` instance) as their first positional argument.

```python
def handle_dcm(dcm):
    print(dcm)

with StoreSCPServer(my_node_info, data_dir=dicom_dir) as server:
    # wait for DICOM and do stuff.
```

Although this is a bit of a hack, you can set some parameters of a function before calling it using the `functools.partial`. For example, you could imagine using a similar function to upload DICOM metadata to a database like this:

```python
import functools

from pacsanini.convert import dcm2dict

from foobar import connection


def handle_dcm(dcm, db_conn_str=""):
    dcm_dict = dcm2dict(dcm)
    conn = connection(db_conn_str)
    conn.upload(dcm_dict)


handle_dcm_partial = functools.partial(handle_dcm, db_conn_str="db://jdoe:password@db.example.com")

with StoreSCPServer(my_node_info, data_dir=dicom_dir, callbacks=[handle_dcm_partial]) as server:
    # wait for DICOM and do stuff.
```
