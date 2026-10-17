import asyncio

from src.worker import EmbeddingWorker

if __name__ == "__main__":
    worker = EmbeddingWorker()
    asyncio.run(worker.run())

# {
#     "event": "EMBEDDING_REQUESTED",
#     "jobId": "967ed47d-094e-4a82-9912-3c7565d99599",
#     "reportId": "e2941bc2-d49b-4414-bb43-09656ffa5099",
#     "description": "A silly lady",
#     "media":{
#         "images": ["https://res.cloudinary.com/ddp01fdd8/image/upload/v1788688858/avatars/mtyiepzrcaszqij0dz20.jpg"],
#         "videos": []
#     }
# }