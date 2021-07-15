# Release process

For maintainers of `pacsanini` that have access to `pypi`, this is how to upload
`pacsanini` to `pypi`:

1. Ensure that you have `poetry` [installed](https://python-poetry.org/docs/#installation)
2. Update the version number in `pacsanini/__version__.py` and `pyproject.toml`
3. Commit the changes with a message of `Version x.y.z` (where x.y.z is the updated version number)
4. Push the changes to [GitHub](https://github.com/Therapixel/pacsanini)
5. Ensure that that your repo is clean by removing previous builds. You can use `make clean`
6. Build the source distribution with `make build` (or `poetry build`)
7. Upload to `pypi` with `make publish` (or `poetry publish`)
8. Add a tag on GitHub corresponding to the newly pushed version number
9. Include a handwritten changelog

### Release schedule

`pacsanini` does not currently follow a regular release schedule. This will be dictated by the contributions that are made to the project.

### Versioning

`pacsanini` does not currently strictly abide by semantic versioning.
Major version changes should be made when code changes break backwards compatibility.
Minor version changes should be made when backwards compatible functionalities are added.
Patch version changes should be made when making a backwards compatible bug fix.
