import asyncio
import json

import aio_pika
from aio_pika import IncomingMessage
from aio_pika.exceptions import ChannelNotFoundEntity

from .config import settings
from .database.service.reportEmbeddingService import save_report_embeddings
from .database.service.similarityService import compute_candidate_scores
from .embedding.clipEmbedder import ClipEmbedder
from .rabbitmq import connect
from .tasks.models import EmbeddingTask


class EmbeddingWorker:
    def __init__(self):
        self.embedder = ClipEmbedder()

    async def process_task(self, message: IncomingMessage):
        async with message.process():
            task = None
            try:
                task = EmbeddingTask(**json.loads(message.body))
                print(f"Processing embedding job: {task.jobId}")

                result = self._process_media(task)
                visual_embeddings = result["images"] + result["videos"]

                # Spring creates the report row. Persist vectors before candidate lookup.
                save_report_embeddings(
                    report_id=task.reportId,
                    text_embedding=result["text"],
                    visual_embeddings=visual_embeddings,
                )
                candidates = compute_candidate_scores(
                    incoming_report_id=task.reportId,
                    search_radius=settings.DUPLICATE_SEARCH_RADIUS_METERS,
                    top_n=settings.DUPLICATE_CANDIDATE_LIMIT,
                )
                await self.publish_completed(task, candidates)
            except Exception as err:
                if task is None:
                    # Malformed messages cannot be correlated to a report.
                    raise
                await self.publish_failed(task, err)
                raise

    def _process_media(self, task: EmbeddingTask):
        image_embeddings = self.embedder.embed_images(task.media.images)
        frame_embeddings = self.embedder.embed_videos(task.media.videos)
        text_embedding = (
            self.embedder.encode_text(task.description)
            if task.description
            else None
        )
        return {
            "images": image_embeddings,
            "videos": frame_embeddings,
            "text": text_embedding,
        }

    async def publish_completed(self, task: EmbeddingTask, candidates: list[dict]):
        event = {
            "event": "EMBEDDING_COMPLETED",
            "jobId": task.jobId,
            "reportId": task.reportId,
            "status": "COMPLETED",
            "candidates": candidates,
        }
        await self.publish_event(event)

    async def publish_failed(self, task: EmbeddingTask, error: Exception):
        await self.publish_event(
            {
                "event": "EMBEDDING_FAILED",
                "jobId": task.jobId,
                "reportId": task.reportId,
                "status": "FAILED",
                "error": str(error),
            }
        )

    async def publish_event(self, event: dict):
        connection = await connect()
        try:
            channel = await connection.channel()
            routing_key = (
                settings.EMBEDDING_FAILED_BINDING
                if event["event"] == "EMBEDDING_FAILED"
                else settings.EMBEDDING_COMPLETED_BINDING
            )
            exchange = await channel.declare_exchange(
                name=settings.EMBEDDING_COMPLETE_EXCHANGE, passive=True
            )
            message = aio_pika.Message(
                body=json.dumps(event).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
            )
            await exchange.publish(message, routing_key=routing_key)
        except ChannelNotFoundEntity:
            print(f"Exchange {settings.EMBEDDING_COMPLETE_EXCHANGE} does not exist")
            raise
        finally:
            await connection.close()

    async def run(self):
        connection = await connect()
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        try:
            queue = await channel.declare_queue(
                settings.RABBITMQ_QUEUE, durable=True, passive=True
            )
            print(f"Listening on {settings.RABBITMQ_QUEUE}")
            await queue.consume(self.process_task)
            await asyncio.Future()
        except ChannelNotFoundEntity:
            print(f"Queue {settings.RABBITMQ_QUEUE} does not exist")
            raise
