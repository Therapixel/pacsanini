# Running the pacsanini pipeline

One of the main objectives `pacsanini` has is to make DICOM data collection and
structuring a piece of cake. As such, the `pacsanini` tool comes packaged with a
pre-defined pipeline flow (using the [prefect](https://docs.prefect.io/) library).

In this pipeline, you will be able to:

1. Identify DICOM resources to retrieve
2. Move said resources to your local node
3. Parse DICOM data in a structured manner

with the execution of a single command.

Before the magic happens, you will have to write a configuration file to instruct the `pacsanini` program how to proceed.

## Using a database

For the purposes of this tutorial, we will be using the following configuration file (which we will refer to as *pacsanini_config.yaml*).

```yaml
net:
  called_node:
    aetitle: MYPACS
    ip: localhost
    port: 104
  dest_node:
    aetitle: pacsanini
    ip: localhost
    port: 11112
  local_node:
    aetitle: pacsanini
    ip: localhost
    port: 11112
find:
  start_date: "20200101"
  end_date: "20210101"
  modality: "MG"
  query_level: STUDY
  search_fields:
  - PatientName
  - StudyInstanceUID
move:
  query_level: STUDY
storage:
  resources: "sqlite:///resources.db"
  directory: "dcmdir"
  sort_by: PATIENT
```

In this example, we will be querying a PACS located on our own machine. We have also configured the `net.dest_node` and `net.local_node` sections that will enable us to communicate with the PACS node and perform Q\R.

We will be querying the PACS for all MG studies that have taken place between the 1<sup>rst</sup> of January 2020 and the the 1<sup>rst</sup> of January 2021.

The C-FIND results will be stored in a sqlite database named `resources.db`. DICOM files will be stored under the `dcmdir` directory.

With the configuration explained, the following command will make sense:

```bash
pacsanini orchestrate -f pacsanini_conf.yaml
```

Note that if the database does not already exist, you can add the following flag:

```bash
pacsanini orchestrate -f pacsanini_conf.yaml --init-db
```

## Using CSV

```yaml
net:
  called_node:
    aetitle: MYPACS
    ip: localhost
    port: 104
  dest_node:
    aetitle: pacsanini
    ip: localhost
    port: 11112
  local_node:
    aetitle: pacsanini
    ip: localhost
    port: 11112
find:
  start_date: "20200101"
  end_date: "20210101"
  modality: "MG"
  query_level: STUDY
  search_fields:
  - PatientName
  - StudyInstanceUID
move:
  query_level: STUDY
storage:
  resources: "resources_found.csv"
  resources_meta: "resources_meta.csv"
  directory: "dcmtest"
  sort_by: PATIENT
tags:
- callback: null
  default_val: null
  tag_alias: image_uid
  tag_name:
  - SOPInstanceUID
- tag_alias: modality
  tag_name: Modality
- callback: null
  default_val: null
  tag_alias: laterality
  tag_name:
  - Laterality
  - ImageLaterality
```

In contrast to the previous database example, we are configuring `pacsanini` to use CSV files for its storage backend. This is done by setting the `storage.resources` item to *resources_found.csv* and the `storage.resources_meta` item to *resources_meta.csv*. The first file is where C-FIND results will be stored. The second file is where the results of the DICOM parsing will be stored.

Another important addition in this file is the presence of a `tags` section. Without it, `pacsanini` will not know which DICOM tags to parse and write to CSV.

Finally, the `move.query_level` and `find.query_level` items must have the same value (*PATIENT* or *STUDY*) for the pipeline to work.

Once such a file is created, execute the pipeline as so:

```bash
pacsanini orchestrate -f pacsanini_conf.yaml
```

If you are expecting large quantities of DICOM data, you may want to speed up the DICOM parsing part. This can be done by adding the following argument:

```bash
pacsanini orchestrate -f pacsanini_conf.yaml --threads 5
```


## Using notifications

The data collection pipeline can be a long running process. To get notified when
a particular task is done, see the [email configuration](../configuration.md#email-configuration)
section on how to setup email notifications
