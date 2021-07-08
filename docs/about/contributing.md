# Contributing to pacsanini

The pacsanini project welcomes contributions from developers and
users in the open source community. Contributions can be made
in a number of ways, a few examples are:

- Code patches via pull requests
- Documentation improvements
- Bug reports and patch reviews
- Feature enhancements

## Code of Conduct

Everyone interacting in the pacsanini project's codebases, issue trackers, chat
rooms, and mailing lists is expected to follow the [PSF Code of Conduct].

## Reporting an Issue

Please include as much detail as you can. Let us know your platform and pacsanini
version. If the problem is visual (for example a theme or design issue) please
add a screenshot and if you get an error please include the full error and
traceback.

## Testing the Development Version

If you want to just install and try out the latest development version of
pacsanini you can do so with the following command. This can be useful if you
want to provide feedback for a new feature or want to confirm if a bug you
have encountered is fixed in the git master. It is recommended that you do
this with a [poetry] inside a [virtual environment].

## Installing for Development

First you'll need to fork and clone the repository. Once you have a local
copy, run the following command. You should do this with [poetry]
within a [virtual environment] and a python version greater or equal to 3.7. To help you set up your environment the following
command remains at your disposal:

```bash
make setup
```

<details>
  <summary>How to install poetry</summary>

  Installing poetry can be done using the following command. For more details,
  see the official documentation [here](https://python-poetry.org/docs/#installation)
  ```bash
  curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
  ```

</details>

## Running the tests

### Running tests for your current python version

Simply run one of the following two commands:

```bash
pytest
# OR
make test
```

### Running tests for multiple python versions

To maintain compatibility over multiple python versions, you should test pacsanini
using [tox](https://tox.readthedocs.io/en/latest/).

To run tests with `tox`, simply do:

```bash
tox
# OR
make tox
```

If you don't have multiple python versions installed on your machine, you can use [pyenv](https://github.com/pyenv/pyenv) to install them without interfering with you system's version(s). Once `pyenv` is installed, you can install the python versions supported by this project (eg: `pyenv install 3.7.10 3.8.10 3.9.5`). Do ensure that these versions will appear in your `$PATH` so that `tox` can find them (tip: `pyenv global 3.7.10 3.8.10 3.9.5`).

## Package management

pacsanini uses [poetry] to manage its dependencies. This means that rather than installing
packages using `pip`, pacsanini developers use `poetry add <package name>` to add a core
dependency and `poetry add -D <package name>` to add a development dependency.

## Submitting Pull Requests

Once you are happy with your changes or you are ready for some feedback, push
it to your fork and send a pull request. For a change to be accepted it will
need to have updated tests and documentation.

[PSF Code of Conduct]: https://www.python.org/psf/conduct/
[poetry]: https://python-poetry.org/
[virtual environment]: https://docs.python.org/3/tutorial/venv.html
