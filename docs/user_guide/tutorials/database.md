# Using a SQL database

## Context

`pacsanini` enables users to store DICOM metadata into SQL databases. The advantage
of doing such a thing is that data stored in a SQL database is centralized and can
be easily accessed from different machines.

In addition, a database system allows you to query your data and read only what you
want. This contrasts with CSV or JSON data files where you would typically need to
read the entire file and then select the rows you want.

Although databases do provide advantages over CSV and JSON, a downfall is that the
data stored in their tables needs to predefined and therefore does not offer the
flexibility that parsing DICOM files with `pacsanini` `DICOMTagGroup` objects offers.

The latter point is believed to be offset by the fact that the application's database
structure is such that the main data table, the `images` table, is denormalized by containing
DICOM attributes other than image level attributes in the DICOM data model (eg: patient ID).
This denormalization has it so that the images table contains some of the most useful
and universal DICOM tag values that can be used for querying data. The addition of a
`meta` column also makes it so that users can query the images table and obtain a JSON
representation of the DICOM image (excluding pixel data) that can then be converted back
to a `pydicom.Dataset` object.

## Setting up the database configuration

To make pacsanini use a database, you simply need to setup your configuration file in the
following way (let's assume that it is named `pacsanini_conf.yaml`):

```yaml
storage:
  resources: "sqlite:///resources.db"
  resources_meta: ""
  directory: ""
```

In this example, we will be telling `pacsanini` to use a sqlite database named *resources.db*.
Note that these are the only configuration options needed to have a functional configuration
in the examples below.

## Initializing the database

Once the configuration file is setup, it is time to create the database and its tables. This
is simply done with the following command line:

```bash
pacsanini db init -f pacsanini_conf.yaml
```

## Inserting DICOM files in the database

Now that the database is setup, it is time to populate it with some data! Let's assume our
DICOM files are stored in a directory named *dicom-data*. This is simply done using the
following command line:

```bash
pacsanini parse -i dicom-data -f pacsanini_conf.yaml --fmt sql
```

When the process is done, you will be able to see the results in the *resources.db* database
by connecting to the database using the `sqlite3` command or by using `pacsanini` code as so:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pacsanini.config import PacsaniniConfig
from pacsanini.db import Image

config = PacsaniniConfig.from_yaml("pacsanini_conf.yaml")
engine = create_engine(config.storage.resources)
DBSession = sessionmaker(bind=engine)
session = DBSession()

for image in session.query(Image).all():
    print(image)
```
