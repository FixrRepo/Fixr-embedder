import json
import aio_pika
import asyncio
from aio_pika import IncomingMessage
from aio_pika.exceptions import ChannelNotFoundEntity

from .config import settings
from .rabbitmq import connect
from .redis import redis
from .embedding.clipEmbedder import ClipEmbedder
from .tasks.resultStore import EmbeddingResultStore
from .tasks.models import EmbeddingTask

class EmbeddingWorker:

    def __init__(self):
        self.embedder = ClipEmbedder()
        self.result_store = EmbeddingResultStore(
            redis=redis, ttl=settings.EMBEDDING_RESULT_TTL
        )

    async def process_task(self, message: IncomingMessage):   

        async with message.process():
        
            task = json.loads(message.body)
        
            task = EmbeddingTask(**task)
            jobId = task.jobId
            print(f"Processing embedding job: {jobId}")

            try:
                print("Processing media")
                result = self._process_media(task)
                
                await self.result_store.store(
                    task=task, imageEmbeddings=result.get("images"), textEmbedding=result.get("text"), 
                    frameEmbeddings=result.get("videos")
                )
                imagesID = [str(embedResult.embeddingId) for embedResult in result.get("images") ] 
                videosID = [str(embedResult.embeddingId) for embedResult in result.get("videos")]   

                task.media.images = imagesID
                task.media.videos = videosID            
                await self.publish_completed(task)

            except Exception as err:
                await self.publish_failed(task, err)
                err.with_traceback()
    

    def _process_media(self, task:EmbeddingTask):
        media = task.media
        imageEmbeddings = []
        videoEmbeddings = []
        textEmbedding = ''

        if len(media.images) > 0:
            imageEmbeddings = self.embedder.embed_images(media.images)

        if len(media.videos) > 0:
            videoEmbeddings = self.embedder.embed_videos(media.videos)
        if len(task.description) > 0:
            textEmbedding = self.embedder.encode_text(task.description)
        return {
            "images": imageEmbeddings,
            "videos": videoEmbeddings,
            "text": textEmbedding
        }        


    async def publish_completed(self, task: EmbeddingTask):
        print(f"Successfully completed task {task.jobId}")
        await self.publish_event({
            "event": "EMBEDDING_COMPLETED",
            "jobId": task.jobId,
            "media": {
                "images": task.media.images,
                "videos": task.media.videos
            },
            "reportId": task.reportId,
        })


    async def publish_failed(self, task:EmbeddingTask, error: Exception):
        await self.publish_event({
                    "event": "EMBEDDING_FAILED",
                    "jobId": task.jobId,
                    "reportId": task.reportId,
                    "error": str(error)
                })

        
    async def publish_event(self, event):
        connection = await connect()
        channel = await connection.channel()
        routingKey = settings.EMBEDDING_FAILED_BINDING if event['event'] == "EMBEDDING_FAILED" else settings.EMBEDDING_COMPLETED_BINDING
        try: 
            exchange = await channel.declare_exchange(name=settings.EMBEDDING_COMPLETE_EXCHANGE, passive=True)
            message = aio_pika.Message(body=json.dumps(event).encode(), 
                                       delivery_mode=aio_pika.DeliveryMode.PERSISTENT, 
                                       content_type="application/json")
            
            await exchange.publish(
                        message,
                        routing_key=routingKey
                    )
            print(f"Successfully dispatched {event}")
        except ChannelNotFoundEntity as e:
            print(f"Error: Exchange {settings.EMBEDDING_COMPLETE_EXCHANGE} does not exist")
            raise


    async def run(self):
        connection = await connect()

        channel = await connection.channel()

        await channel.set_qos(prefetch_count=1)

        try:
            queue = await channel.declare_queue(settings.RABBITMQ_QUEUE, durable=True, passive=True)
            
            print(f"Listening on {settings.RABBITMQ_QUEUE}")
            await queue.consume(self.process_task)
            await asyncio.Future()

        except ChannelNotFoundEntity as e:
            print(f"Error: Queue {settings.RABBITMQ_QUEUE} does not exist")
            raise