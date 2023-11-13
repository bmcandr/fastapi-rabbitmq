FROM python:3.10-slim as builder

WORKDIR /app

COPY scripts/wait-for-it.sh .

COPY pyproject.toml .

FROM builder as consumer

RUN python -m pip install .

FROM builder as producer_consumer

RUN python -m pip install .["producer_consumer"]
