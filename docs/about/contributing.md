# Contributing to pacsanini

The `pacsanini` project welcomes contributions from all developers and users in the open source community.
Contributions can be made in a number of ways. A few examples are:

* Code patches via pull requests
* Documentation improvements
* Bug reports and patch reviews
* Feature enhancement proposals

## Code of Conduct

Please refer to `pacsanini`'s [Code of Conduct](code_of_conduct.md) to learn about the values we adhere to and promote.

## Reporting Issues and Submitting PRs

We are always happy to receive pull requests. Before opening one, please ensure that you have opened an issue so that the rationale for your changes can be better understood by the community.

### Reporting Issues

When submitting an issue, please be as detailed as possible. We use [GitHub issues](https://github.com/Therapixel/pacsanini/issues) to track requests and bugs.

If the issue a code bug, please follow the guidelines provided in this excellent [blog post](https://matthewrocklin.com/blog/work/2018/02/28/minimal-bug-reports).

### Submitting PRs

Before submitting PRs to [GitHub](https://github.com/Therapixel/pacsanini/pulls), please ensure that the changes provided by your contributions are tested (see the [running tests](#running-tests) section). Although test suites are automatically run when you will submit the PR, it is easier for the reviewer to review it when there is less trouble.

## Setting Up Your Environment

To get started with the development of `pacsanini`, you'll first need to fork and clone the repository.

Once you have a local copy, make sure that you are using a python version greater or equal to `3.7` (preferably within a virtual environment). You should ensure that you have installed [poetry](https://python-poetry.org/) in that python environment.

<details>
  <summary>How to install poetry</summary>

  Installing poetry can be done using the following command. For more details,
  see the official documentation [here](https://python-poetry.org/docs/#installation)
  ```bash
  curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
  ```

</details>

At that point, you can simply run `make setup`. This will instruct `poetry` to install all the dependencies you need and setup your `pre-commit` hooks. At that point, you'll have the good python environment to start developing!

To simplify the setup process you can run `make setup`.

<details>
  <summary>Why pre-commit hooks?</summary>

  Pre-commit hooks are in place so that we can focus on what we actually want to do: develop. The pre-commit hooks take care of our coding style (`black` and `isort`) and also ensure that we didn't forget to resolve a merge conflict for example. We find that rather than trying to enforce rules and guidelines as humans, we are much better off letting machines (with whom it's hard to argue with) dictate these things.

</details>

## Running tests

Although tests are automatically run when new pull requests are submitted, you are encouraged to run tests locally. Testing is done with the `pytest` framework. This is useful for running quick tests.

```bash
make test
# or
# pytest -m <name of testing module>
# or
# pytest tests/my/file_test.py
```

When you are ready to submit your pull request, run the project's tests using [tox](https://tox.readthedocs.io/en/latest/). This allows testing the project against the multiple supported python versions.

```bash
make tox
# or
# tox
```

## Updating Dependencies

If dependencies need to be updated in the project, you should use `poetry`. If the dependency you are updating or adding impacts the project's core code, use `poetry add <package_name>`. If the dependency is for development purposes (eg: testing or linting), use `poetry add -D <package_name>`.
