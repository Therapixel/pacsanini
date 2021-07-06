# pacsanini

`pacsanini` 🎻 is a package designed to help with the collection of DICOM files and the extraction of DICOM tags (metadata) for structuring purposes.

## Overview

`pacsanini`'s functionalities come out of a desire to facilitate research in
medical imagery by easing the process of data collection and structuring.

The two main pain points for this are:

* acquiring data from a PACS
* extracting metadata from DICOM files in research-ready formats (eg: csv)

## Installation and Deployment

`pacsanini` can be installed using in one of the following ways:

### poetry

This is the preferred way to install the project's dependencies. This way also
allows you to install dev dependencies. See [here](https://python-poetry.org/docs/#installation)
on how to install poetry.

```bash
poetry install --no-root --no-dev
# or, to install the project and its development dependencies:
poetry install --no-root
```

### pip

```bash
git clone https://github.com/Therapixel/pacsanini.git
cd pacsanini
pip install .
```

### docker

A docker image can be built locally to run `pacsanini` within an isolated environment.

```bash
docker image build -t latest .
docker run pacsanini --help
```

## Roadmap

### Data Collection

* 🚧 Make single-command pipeline more mature.
  * Add a feature to send notifications when a step is done

* 🚧 Use sql storage as an alternative to CSV storage.

### Testing

🚧 Find a good way to test DICOM network messaging applications. Possibly with the
`dcmtk` suite, the apps from `pynetdicom` or even a Docker container with a PACS?
