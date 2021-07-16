[![Documentation Status](https://readthedocs.org/projects/pacsanini/badge/?version=latest)](https://pacsanini.readthedocs.io/en/latest/?badge=latest)
![GitHub](https://img.shields.io/github/license/Therapixel/pacsanini) ![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/Therapixel/pacsanini)

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

## Installation

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
docker image build -t latest .
docker run pacsanini --help
```

## Roadmap

The following topics are the main areas where `pacsanini` can improve as a library and a tool.
Of course, these topics are up for discussion and such discussions are encouraged in the
[GitHub issues](https://github.com/Therapixel/pacsanini/issues) section.

### Documentation

* 🚧 Provide more in-depth examples of how `pacsanini` can be used and be useful inside
  python applications

### Data Collection

* 🚧 Make the single-command pipeline more mature.
  * Add a feature to send notifications when a step is done

* 🚧 Use sql storage as an alternative to CSV storage.

* 🚧 Improve error handling for C-MOVE operations.

* 🚧 Implement the ability for event handling when DICOM files are received by the storescp server.

### Testing

* 🚧 Find a good way to test DICOM network messaging applications. Possibly with the
  `dcmtk` suite, the apps from `pynetdicom` or even a Docker container with a PACS?
