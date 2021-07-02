# Collection

## Scenario

You wish to collect and structure data from your own PACS or a partners' PACS.
This assumes that you have have installed pacsanini and are familiar with pacsanini
configuration files.

Given the configuration file setup, the collection process will then go as follows:

1. Find the DICOM resources that are stored in the target PACS
2. Request the DICOM resources and:
    * Parse the resources' DICOM tags
    * Write the collected DICOM files to disk

## Environment Setup

The idea behind the configuration file is that you are able to store all of your
settings in one place and re-use those same settings during the entire collection
process.

For the purposes of this guide, let's assume that we will be using the following
configuration file (saved under `pacsaniniconf.yaml`):

=== "YAML"

    ``` yaml
    move:
        start_time: 20:00
        end_time: 08:00
        query_level: STUDY
    net:
        local_node:
            aetitle: mytitle
            port: 11112
        called_node:
            aetitle: theirtitle
            ip: 127.0.0.1
            port: 11112
    find:
        query_level: STUDY
        search_fields:
            - StudyInstanceUID
            - PatientID
        start_date: "20200101"
        end_date: "20201212"
        modality: CT
    storage:
        resources: my/resources.csv
        directory: my/dicom/dir
        sort_by: PATIENT
    tags:
        - tag_name: PatientName
          callback: str
        - tag_name: StudyDate
          tag_alias: study_date
          callback: pacsanini.convert:str2datetime
        - tag_name: Laterality
          default_val: U
          callback: str
        - tag_name: StudyInstanceUID
        - tag_name: SOPInstanceUID
    ```

=== "JSON"

    ``` json
    {
        "move": {
            "start_time": "20:00",
            "end_time": "08:00",
            "query_level": "STUDY"
        },
        "net": {
            "local_node": {
                "aetitle": "mytitle",
                "port": 11112
            },
            "called_node": {
                "aetitle": "theirtitle",
                "ip": "127.0.0.1",
                "port": 11112
            }
        },
        "find": {
            "query_level": "STUDY",
            "search_fields": ["StudyInstanceUID", "PatientID"],
            "start_date": "20200101",
            "end_date": "20201212",
            "modality": "CT"
        },
        "storage": {
            "resources": "my/resources.csv",
            "directory": "my/dicom/dir",
            "sort_by": "PATIENT"
        },
        "tags": [
            {
                "tag_name": "PatientName",
                "callback": "str"
            },
            {
                "tag_name": "StudyDate",
                "tag_alias": "study_date",
                "callback": "pacsanini.convert:str2datetime"
            },
            {
                "tag_name": "Laterality",
                "default_val": "U",
                "callback": "str"
            },
            {
                "tag_name": "StudyInstanceUID"
            },
            {
                "tag_name": "SOPInstanceUID"
            }
        ]
    }
    ```

## Collecting Resources

To collect resources, simply run the following commands in a terminal:

```bash
pacsanini find -f pacsaniniconf.yaml
pacsanini move -f pacsaniniconf.yaml
```

With these two commands, you have just been able to:

1. Find all the computed tomography (CT) resources stored on the PACS between the first of
   January 2021 and the 12th of December 2021 (`pacsanini find -f pacsaniniconf.yaml`); and
2. Request the found resources from the PACS and store them on disk (`pacsanini move -f pacsaniniconf.yaml`).
