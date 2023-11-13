# FastAPI + RabbitMQ Demo

An demo/exploration of the pub-sub messaging pattern with FastAPI and RabbitMQ (via `aio_pika`).

Includes:

* A FastAPI app that serves as both a publisher and consumer (`src/producer_consumer/main.py`).
* A standalone consumer app (`src/consumer/main.py`).
* A `docker-compose.yml` file for standing up a RabbitMQ service and running the above apps.

## Run

**Note:** requires Docker.

1. Start the services with `docker compose up` and wait for them to come online (15-20s).
2. Navigate to `localhost:8000/docs` in your browser.
3. Send messages with the `publish` endpoint and watch the logs as either the `producer_consumer` FastAPI app or the `consumer` app consumes and processes each message. Alternately, run `sh scripts/emit-events.sh` to send 20 messages.
4. List the message log with the `/log` endpoint.
