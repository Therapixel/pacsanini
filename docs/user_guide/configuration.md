# Configuration

`pacsanini` strives to be a library that developers can use and extend in their
own code as well as a full-fledged command line tool. To avoid passing a
myriad of arguments and options to commands, the preferred solution is to
use a configuration file. Depending on the uses you have of pacsanini, sections
may be omitted.

## Outline

Configuration files can be in `YAML` or `JSON` format.

=== "YAML"

    ``` yaml
    move:
        start_time: 20:00
        end_time: 06:00
        query_level: STUDY
    net:
        local_node:
            aetitle: mytitle
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
            "end_time": "06:00",
            "query_level": "STUDY"
        },
        "net": {
            "local_node": {
                "aetitle": "mytitle"
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

The table below illustrates which configuration sections are required to perform the
functionalities that pacsanini offers from the command line.

| Command | move | net | find | storage | tags |
| ------- | ---- | --- | ---- | ------- | ---- |
| config | :material-close: | :material-close: | :material-close: | :material-close: | :material-close: |
| parse   | :material-close: | :material-close: | :material-close: | :material-close: | :material-check: |
| parse-conf | :material-close: | :material-close: | :material-close: | :material-close: | :material-close: |
| server  | :material-close: | :material-check: | :material-close: | :material-check: | :material-close: |
| echo    | :material-close: | :material-check: | :material-close: | :material-close: | :material-close: |

## Setup

To get started with a configuration file, run the following command:

```bash
pacsanini config pacsaninirc.yaml
```

This will generate a template configuration named `pacsaninirc.yaml`. To check out it's contents
and edit it, run:

```bash
pacsanini config pacsaninirc.yaml --edit
```

Once you're happy with the changes you've made, exit your editor and start taking
advantage of `pacsanini`'s functionalities.

## Understanding sections

### move configuration

=== "YAML"

    ``` yaml
    move:
        start_time: 20:00
        end_time: 06:00
        query_level: STUDY
    ```

=== "JSON"

    ``` json
    {
        "move": {
            "start_time": "20:00",
            "end_time": "06:00",
            "query_level": "STUDY"
        }
    }
    ```

The `move` configuration indicates what rules to following when actually performing
query retrieve operations from a PACS. The `start_time` and `end_time` are optional
and should either both be present or both be absent from the configuration file. These
are used to indicate when query retrieve operations should be instructed to the PACS
in order to avoid saturing its network and hindering on normal operations. If the
`start_time` is greater than the `end_time` (as in this example), this means that queries
sohuld only happen between the specified start time on day 1 and the specified end time
on day 2.

The `query_level` setting indicates the request level to adopt when querying the PACS
for DICOM files.

### net configuration

=== "YAML"

    ``` yaml
    net:
        local_node:
            aetitle: mytitle
        called_node:
            aetitle: theirtitle
            ip: 127.0.0.1
            port: 11112
    ```

=== "JSON"

    ``` json
    {
        "net": {
            "local_node": {
                "aetitle": "mytitle"
            },
            "called_node": {
                "aetitle": "theirtitle",
                "ip": "127.0.0.1",
                "port": 11112
            }
        }
    }
    ```

The `net` configuration section indicates to the application what your DICOM
node information is with the `local_node` value. Only the `aetitle` value is
required. The `port` parameter will be needed if you wish to run a storescp
server.

The `called_node` value corresponds to the information regarding the DICOM node
you are trying to communicate with (eg: a PACS). Here, the `aetitle`, `ip`, and
`port` values are all required.

By default, the `dest_node` value, if unset, is equal to the `local_node` value.
This is used for C-MOVE operations in which case the `aetitle` and `port` values
must be specified.

### find configuration

=== "YAML"

    ``` yaml
    find:
        query_level: STUDY
        search_fields:
            - StudyInstanceUID
            - PatientID
        start_date: "20200101"
        end_date: "20201212"
        modality: CT
    ```

=== "JSON"

    ``` json
    {
        "find": {
            "query_level": "STUDY",
            "search_fields": ["StudyInstanceUID", "PatientID"],
            "start_date": "20200101",
            "end_date": "20201212",
            "modality": "CT"
        }
    }
    ```

The `find` configuration is used to provide instructions on what data you
wish to retrieve from a PACS. The `query_level`, `search_fields`, and `start_date`
parameters are required for this. You may also specify the `end_date` parameter
to indicate that you want to collect results between the `start_date` and the
`end_date`. The `modality` parameter may also be used to specify that you want
to retrieve results for only a specific type of DICOM modality.

!!! info
    For the `find` configuration to be useful, you will also need to have a
    properly configured [net section](#net-configuration).

### storage configuration

=== "YAML"

    ``` yaml
    storage:
        resources: my/resources.csv
        directory: my/dicom/dir
        sort_by: PATIENT
    ```

=== "JSON"

    ``` json
    {
        "storage": {
            "resources": "my/resources.csv",
            "directory": "my/dicom/dir",
            "sort_by": "PATIENT"
        }
    }
    ```

The `resources` configuration is used to indicate where to store DICOM resources
obtained by running `C-FIND` requests and which resources you want to ask the PACS
to retrieve when running `C-MOVE` requests.

The `storage` configuration is used to indicate where to indicate where to store
DICOM files received from settting up a storesecp server or from C-MOVE requests.

The `sort_by` value indicates how to store results. Possible values are `PATIENT`
(ie: `<directory>/<patientID>/<studyUID>/<seriesUID>/<imageUID>.dcm`), `STUDY`
(ie: `<directory>/<studyUID>/<seriesUID>/<imageUID>.dcm`), or `IMAGE`
(ie: `<directory>/<imageUID>.dcm`).

!!! info
    For the `storage` configuration to be useful, you will also need to have a
    properly configured [net section](#net-configuration).

### tags configuration

=== "YAML"

    ``` yaml
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

The `tags` configuration section indicates which DICOM tag values you wish to
retrieve from DICOM files you have collected.

The `tag_name` parameter can be a single tag name or a list of tag names (for
example *Laterality* and *ImageLaterality*). For nested tags, you can use the
following syntax: `<parent_tag>.<child_tag>` (eg: *ViewCodeSequence.Code*).
When results are written to disk, the column name for the parsed tag will correspond
to the tag_name value you provided. If you want an alias for this, specify a
`tag_alias` value. If you are trying to parse optional DICOM tags but want a
default value to be returned other than None, specify the `default_val` parameter.
To apply formatting to parsed DICOM tag values, you can specify a data type or
a function (which must be available in your PYTHONPATH). When specifying a
custom function, the string must be in the following format: `<module>.<submodule>:<function>`.
