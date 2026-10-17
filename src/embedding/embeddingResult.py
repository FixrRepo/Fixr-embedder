from dataclasses import dataclass
from torch import Tensor
from uuid import UUID

@dataclass
class EmbeddingResult:
    embedding: Tensor
    text_embedding: Tensor | None
    frame_embeddings:Tensor | None = None

@dataclass
class EmbeddingsResults:
    embeddingId: UUID
    embedding: Tensor
