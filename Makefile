export PYTHONPATH := src:$(PYTHONPATH)
GIT_COMMIT = $(shell git rev-parse --short HEAD)


.DEFAULT_GOAL = help
.PHONY = help build build-exe clean clean-build clean-docs clean-tests clean-pyc docs docs-serve format install lint setup test tox

help:  ## Print this message and exit.
	@IFS=$$'\n' ; \
	help_lines=(`fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##/:/'`); \
	printf "%-30s %s\n" "target" "help" ; \
	printf "%-30s %s\n" "------" "----" ; \
	for help_line in $${help_lines[@]}; do \
		IFS=$$':' ; \
		help_split=($$help_line) ; \
		help_command=`echo $${help_split[0]} | sed -e 's/^ *//' -e 's/ *$$//'` ; \
		help_info=`echo $${help_split[2]} | sed -e 's/^ *//' -e 's/ *$$//'` ; \
		printf '\033[36m'; \
		printf "%-30s %s" $$help_command ; \
		printf '\033[0m'; \
		printf "%s\n" $$help_info; \
	done

archive: clean ## Archive the project using git archive.
	git archive --format=zip --output=pacsanini.zip "$(GIT_COMMIT)"

build:  ## Build the package, as a tarball and a wheel.
	poetry build

build-exe:  ## Build the package, as an executable (using pyinstaller). Don't do inside a virtualenv.
	python -O scripts/build-exe.py

clean: clean-build clean-docs clean-tests clean-pyc  ## Clean up all types of project builds.

clean-build:  ## Clean up previously built project files.
	rm -rf build/ dist/ *.egg-info *.spec src/*.spec

clean-docs:  ## Clean up previously built docs.
	rm -rf site/

clean-tests:  ## Clean all test result and caching files.
	rm -rf .coverage .pytest_cache/ htmlcov/ .tox/ .mypy_cache/

clean-pyc:  ## Clean all __pycache__ and .pyc files.
	rm -rf __pycache__/ ; \
	find tests src/pacsanini -type d -name "__pycache__" -exec rm -rf {} + ; \
	find tests src/pacsanini -type f -name "*.pyc" -exec rm -rf {} + ;

docs: clean-docs  ## Build the project's documentation.
	mkdocs build --strict

docs-serve:  ## Start a server to serve the docs.
	mkdocs serve --strict

format:  ## Format the project's code.
	autoflake --remove-all-unused-imports --recursive --in-place --exclude=__init__.py src/pacsanini tests ; \
	black src/pacsanini tests ; \
	isort src/pacsanini tests ;

install:  ## Install the project as a python package in your environment.
	poetry install --no-dev

lint:  ## Apply linting and formatting to the project's code.
	pylint src/pacsanini tests
	mypy

setup:  ## Setup the development environment (requires poetry).
	poetry install --no-root
	pre-commit install

test: clean-pyc clean-tests  ## Run tests using pytest.
	pytest

tox: clean-pyc clean-tests  ## Run tests using tox to test against multiple python versions.
	tox
