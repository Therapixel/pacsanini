[![Documentation Status](https://readthedocs.org/projects/pacsanini/badge/?version=latest)](https://pacsanini.readthedocs.io/en/latest/?badge=latest)

# pacsanini

`pacsanini` 🎻 is a package designed to help with the collection of DICOM files and the extraction of DICOM tags (metadata) for structuring purposes.

## Overview

`pacsanini`'s functionalities come out of a desire to facilitate research in
medical imagery by easing the process of data collection and structuring.

The two main pain points for this are:

* acquiring data from a PACS
* extracting metadata from DICOM files in research-ready formats (eg: csv)

## Documentation

Check out the complete documentation on [readthedocs](https://pacsanini.readthedocs.io/en/latest/).

## Installation and Deployment

`pacsanini` is only available for python versions 3.7+. The dependency/package management tool used by this project is `poetry`. This is what you need for development.

<details>
  <summary>How to install poetry</summary>

  Installing poetry can be done using the following command. For more details,
  see the official documentation [here](https://python-poetry.org/docs/#installation)
  ```bash
  curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
  ```

</details>

## pacsanini as a package

The following methods are available to install `pacsanini` as a package:

* pip:

```bash
pip install git+https://github.com/Therapixel/pacsanini.git
```

* poetry:

```bash
poetry add git+https://github.com/Therapixel/pacsanini.git
```

## pacsanini for development

`poetry` is the only supported build tool for installing `pacsanini` in a development context.
See the previous section on how to install `poetry`.

```bash
git clone https://github.com/Therapixel/pacsanini.git
cd pacsanini
poetry install --no-root --no-dev
# or, to install the project and its development dependencies:
poetry install --no-root
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
