import json
from redis.asyncio import Redis
from ..tasks.models import EmbeddingTask
from ..embedding.serialization import serialize_tensor
from ..embedding.embeddingResult import EmbeddingsResults
class EmbeddingResultStore:
    def __init__(self, redis:Redis, ttl:int):
        self.redis = redis
        self.ttl = ttl

    def _key(self, jobId: str):
        return f"embedding:job:{jobId}"

    async def store(self, task: EmbeddingTask, imageEmbeddings: list[EmbeddingsResults], textEmbedding, frameEmbeddings: list[EmbeddingsResults]):
        key = self._key(task.jobId)
        metadata = {
            "jobId": task.jobId,
            "reportId": task.reportId,
            "media": json.dumps({
                "images": task.media.images,
                "videos": task.media.videos
            }),
            "status": "COMPLETED"
        }

        async with self.redis.pipeline() as pipe:
            pipe.hset(key, mapping=metadata)

            if len(imageEmbeddings) > 0:
                for image in imageEmbeddings:
                    pipe.hset(key,  f"imageEmbedding:{image.embeddingId}", serialize_tensor(image.embedding))

            if textEmbedding is not None:
                pipe.hset(key, "textEmbedding", serialize_tensor(textEmbedding))

            if len(frameEmbeddings) > 0:
                for video in frameEmbeddings:
                    pipe.hset(key, f"videoEmbedding:{video.embeddingId}", serialize_tensor(video.embedding))

            pipe.expire(key, self.ttl)

            await pipe.execute()