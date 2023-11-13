import asyncio
import json
import logging
import random
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

import aio_pika
from common.enums import State
from common.schemas import Message
from common.settings import settings
from fastapi import Depends, FastAPI, status
from fastapi.exceptions import HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

PREFECTH_COUNT = 100

MSG_LOG = dict()


async def get_amqp_connection() -> aio_pika.abc.AbstractConnection:
    """Connect to AMQP server."""
    return await aio_pika.connect_robust(str(settings.AMQP_URL))


async def declare_queue(
    channel: aio_pika.abc.AbstractChannel,
    queue: str,
    **kwargs,
) -> aio_pika.abc.AbstractQueue:
    """Create AMQP queue."""
    return await channel.declare_queue(name=queue, auto_delete=True, **kwargs)


async def get_channel(
    connection: aio_pika.abc.AbstractConnection = Depends(get_amqp_connection)
) -> AsyncGenerator[aio_pika.abc.AbstractChannel, None]:
    """Connect to and yield a AMQP channel.

    :yield: RabbitMQ channel.
    """
    async with connection:
        channel = await connection.channel()
        await declare_queue(channel=channel, queue=settings.QUEUE)
        yield channel


async def process_message(message: aio_pika.abc.AbstractIncomingMessage):
    """Do something with the message.

    :param message: A message from the queue.
    """
    try:
        async with message.process(requeue=True):
            logger.info(f"MESSAGE RECEIVED: {message.message_id}")
            msg = Message(**json.loads(message.body.decode()))
            MSG_LOG[message.message_id].update(
                state=State.RECEIVED, received_at=datetime.now()
            )
            duration = random.randint(1, 10)
            await asyncio.sleep(duration)
            logger.info(
                f"MESSAGE CONSUMED: {message.message_id} -- {msg.body} (duration {duration})"
            )
            MSG_LOG[message.message_id].update(
                state=State.CONSUMED,
                consumed_at=datetime.now(),
                duration=duration,
            )
    except Exception as e:
        logger.error(e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start internal message consumer on app startup."""
    connection = await aio_pika.connect_robust(str(settings.AMQP_URL))

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=PREFECTH_COUNT)
        queue = await declare_queue(channel=channel, queue=settings.QUEUE)
        await queue.consume(process_message)

        yield


app = FastAPI(lifespan=lifespan)


@app.get("/log")
def _():
    return MSG_LOG


async def publish_message(
    message: str,
    channel: aio_pika.abc.AbstractChannel,
):
    """Publish a message to the event queue.

    :param message: A message to publish.
    :param channel: The AMQP channel to publish the message to.
    """
    msg = aio_pika.Message(
        body=Message(body=message).model_dump_json().encode(),
        message_id=str(uuid.uuid4()),
    )
    await channel.default_exchange.publish(
        msg,
        routing_key=settings.QUEUE,
    )

    return msg


@app.get(
    "/publish",
    status_code=status.HTTP_202_ACCEPTED,
    description="Publish a message to the event queue.",
)
async def _(
    message: str = "Hello world!",
    channel: aio_pika.abc.AbstractChannel = Depends(get_channel),
):
    """Publish the provided message to the event queue.

    :param message: A message to publish, defaults to "Hello world!".
    :param channel: The AMQP channel to publish the message to
    (provided via `Depends(get_channel)`).
    """
    msg = await publish_message(channel=channel, message=message)
    MSG_LOG[msg.message_id] = dict(
        message=message,
        state=State.PUBLISHED,
        published_at=datetime.now(),
    )

    return {
        "status": "OK",
        "details": {
            "body": message,
            "event_id": msg.message_id,
        },
    }


@app.put("/update")
async def _(message_id: str, state: State):
    try:
        MSG_LOG[message_id].update(
            **{
                "state": state,
                f"{state.lower()}_at": datetime.now(),
            }
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message ID {message_id} not found!",
        )
