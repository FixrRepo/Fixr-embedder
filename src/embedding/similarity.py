import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def calculate_visual_score(
    new_embeddings: list[np.ndarray],
    existing_embeddings: list[np.ndarray],
) -> float | None:
    """Return the mean best cosine match for each incoming vector.

    Embeddings are vectors rather than ORM records. ``None`` distinguishes a
    report with no comparable visual evidence from a genuine score of zero.
    """
    if not new_embeddings or not existing_embeddings:
        return None

    new_vectors = np.asarray(new_embeddings, dtype=np.float32)
    existing_vectors = np.asarray(existing_embeddings, dtype=np.float32)

    if new_vectors.ndim == 1:
        new_vectors = new_vectors.reshape(1, -1)
    if existing_vectors.ndim == 1:
        existing_vectors = existing_vectors.reshape(1, -1)
    if new_vectors.ndim != 2 or existing_vectors.ndim != 2:
        raise ValueError("Embeddings must be one- or two-dimensional vectors")
    if new_vectors.shape[1] != existing_vectors.shape[1]:
        raise ValueError("Embedding vectors must have matching dimensions")
    if not np.isfinite(new_vectors).all() or not np.isfinite(existing_vectors).all():
        raise ValueError("Embedding vectors must contain only finite values")

    similarities = cosine_similarity(new_vectors, existing_vectors)
    return float(similarities.max(axis=1).mean())
