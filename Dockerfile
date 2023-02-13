FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONUNBUFFERED=true
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV POETRY_VERSION=1.3.0
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN python -c 'from urllib.request import urlopen; print(urlopen("https://install.python-poetry.org").read().decode())' | python -

ADD . /app

RUN poetry install --no-interaction --no-ansi -vvv

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=true
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app /app

ENTRYPOINT ["python", "tfeed/app.py"]
