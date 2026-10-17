import aio_pika
from .config import settings


async def connect():
    return await aio_pika.connect_robust(settings.RABBITMQ_URL)