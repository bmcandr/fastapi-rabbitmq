import asyncio
import json
import logging
import random

import aio_pika
import requests
from common.enums import State
from common.schemas import Message
from common.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

PREFECTH_COUNT = 100

APP_URL = "http://producer:8000"


async def process_message(message: aio_pika.abc.AbstractIncomingMessage):
    """Do something with the message.

    :param message: A message from the queue.
    """
    try:
        async with message.process(requeue=True):
            """
            If an error occurs within this context manager,
            the message will be picked up by another consumer.
            """
            logger.info(f"MESSAGE RECEIVED: {message.message_id}")
            # update app
            params = dict(
                message_id=message.message_id,
                state=State.RECEIVED,
            )
            requests.put(f"{APP_URL}/update", params=params)

            # unpack Message
            msg = Message(**json.loads(message.body.decode()))

            # simulate processing delay
            duration = random.randint(1, 10)
            await asyncio.sleep(duration)

            logger.info(
                f"MESSAGE CONSUMED: {message.message_id} -- {msg.body} (duration {duration})"
            )
            # update app
            params = dict(
                message_id=message.message_id,
                state=State.CONSUMED,
            )
            requests.put(f"{APP_URL}/update", params=params)
    except Exception as e:
        logger.error(e)


async def consume():
    """Asynchronously consume a message from an AMQP queue."""
    connection = await aio_pika.connect_robust(str(settings.AMQP_URL))

    channel = await connection.channel()
    await channel.set_qos(prefetch_count=PREFECTH_COUNT)
    queue = await channel.declare_queue(name=settings.QUEUE, auto_delete=True)
    await queue.consume(process_message)

    try:
        await asyncio.Future()
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(consume())
