FROM python:3.10-slim as builder

WORKDIR /app

COPY pyproject.toml .

FROM builder as consumer

RUN python -m pip install .

FROM builder as producer_consumer

RUN python -m pip install .["producer_consumer"]
