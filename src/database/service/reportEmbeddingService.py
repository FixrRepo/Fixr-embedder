from uuid import UUID

import numpy as np
from ..database import SessionLocal
from ..models.reportembedding import ReportEmbedding
from ..models.visualembedding import VisualEmbedding


def _vector_values(embedding) -> list[float]:
    if hasattr(embedding, "detach"):
        embedding = embedding.detach().cpu().numpy()
    values = np.asarray(embedding, dtype=np.float32).reshape(-1)
    if not np.isfinite(values).all():
        raise ValueError("Embedding vector contains non-finite values")
    return values.tolist()


def save_report_embeddings(report_id: str, text_embedding, visual_embeddings) -> None:
    """Replace a Spring-created report embedding's vectors idempotently."""
    report_embedding_id = UUID(str(report_id))
    with SessionLocal.begin() as session:
        report_embedding = session.get(ReportEmbedding, report_embedding_id)
        if report_embedding is None:
            raise LookupError(f"Report embedding not found for report {report_id}")

        if text_embedding is not None:
            report_embedding.text_embedding = _vector_values(text_embedding)

        # Replacing the collection deletes old rows through delete-orphan cascade,
        # so retries cannot append duplicate vectors.
        report_embedding.visual_embeddings = [
            VisualEmbedding(
                id=visual.embeddingId,
                embedding=_vector_values(visual.embedding),
            )
            for visual in visual_embeddings
        ]
