FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

ADD . /app

WORKDIR /app/src
ENV PYTHONPATH=/app/src

ENTRYPOINT ["python", "main.py"]
