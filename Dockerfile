FROM python:3.9.6-slim-buster

RUN apt-get update \
    && apt-get upgrade \
    && apt-get -y install --no-install-recommends curl

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python \
    && cd /usr/local/bin \
    && ln -s /opt/poetry/bin/poetry \
    && poetry config virtualenvs.create false

RUN apt-get -y remove curl \
    && apt-get -y clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/
COPY ./pyproject.toml ./poetry.lock ./src ./

RUN poetry install --no-root --no-dev
ENV PYTHONPATH="/app/"

ENTRYPOINT [ "python", "pacsanini" ]
