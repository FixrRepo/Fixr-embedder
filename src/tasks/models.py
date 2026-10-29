from __future__ import annotations

from dataclasses import dataclass

@dataclass
class EmbeddingTask:

    def __post_init__(self):
        if isinstance(self.media, dict):
            self.media = MediaEmbeddingTask(**self.media)

    jobId:str
    event: str
    reportId:str
    media: MediaEmbeddingTask
    description: str

@dataclass
class MediaEmbeddingTask:
    images: list[str]
    videos: list[str]

