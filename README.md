![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pacsanini)
![PyPI](https://img.shields.io/pypi/v/pacsanini)
![PyPI - Status](https://img.shields.io/pypi/status/pacsanini)
[![Documentation Status](https://readthedocs.org/projects/pacsanini/badge/?version=latest)](https://pacsanini.readthedocs.io/en/latest/?badge=latest)
![GitHub](https://img.shields.io/github/license/Therapixel/pacsanini)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/Therapixel/pacsanini/pacsanini%20run%20tests%20for%20PR)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/Therapixel/pacsanini)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

# pacsanini

`pacsanini` 🎻 is a package designed to help with the collection of DICOM files and the extraction
of DICOM tags (metadata) for structuring purposes.

`pacsanini`'s functionalities come out of a desire to facilitate research in
medical imagery by easing the process of data collection and structuring.
The two main pain points for this are:

* acquiring data from a PACS
* extracting metadata from DICOM files in research-ready formats (eg: csv)

The project seeks to target medical/research professionals that are not necessarily
familiar with coding but wish to obtain data sets and software engineers that wish to
build applications with a certain level of abstraction.

## Documentation

Check out the complete documentation on [readthedocs](https://pacsanini.readthedocs.io/en/latest/).
You will be able to find examples on how to use the `pacsanini` API from within you Python application
and as a command line tool.

## Contributing and Code of Conduct

All contributions to improve `pacsanini` are welcome and valued. For more information on how you can contribute,
please read the [Contributing](CONTRIBUTING.md) document and make sure that you are familiar with our
[Code of Conduct](CODE_OF_CONDUCT.md).

You are also more than welcome to open a discussion on our [GitHub discussions](https://github.com/Therapixel/pacsanini/discussions) page.

## Installation

To install a particular release version, check out the available versions of `pacsanini` on [PyPI](https://pypi.org/project/pacsanini/)
or simply run the following command to obtain the latest release:

```bash
pip install pacsanini
```

To obtain the cutting edge version of `pacsanini`, you can use `pip` or `poetry` in the following way:

```bash
pip install git+https://github.com/Therapixel/pacsanini.git
# or
poetry add git+https://github.com/Therapixel/pacsanini.git
```
### For development

`poetry` is the only supported build tool for installing `pacsanini` in a development context.
See the previous section on how to install `poetry`.

```bash
git clone https://github.com/Therapixel/pacsanini.git
cd pacsanini
poetry install --no-root --no-dev
# or, to install the project and its development dependencies:
poetry install --no-root
```

### Usage with docker

A docker image can be built locally to run `pacsanini` within an isolated environment.

```bash
docker image build -t pacsanini:latest .
docker run pacsanini --help
```

## Roadmap

The following topics are the main areas where `pacsanini` can improve as a library and a tool.
Of course, these topics are up for discussion and such discussions are encouraged in the
[GitHub issues](https://github.com/Therapixel/pacsanini/issues) section.
