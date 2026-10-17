import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def calculate_visual_score(
    new_embeddings: list[np.ndarray],
    existing_embeddings: list[np.ndarray],
) -> float:
    if not new_embeddings or not existing_embeddings:
        return 0.0

    new_vectors = np.stack(new_embeddings)
    existing_vectors = np.stack(existing_embeddings)

    # Rows = new embeddings; columns = existing embeddings.
    similarities = cosine_similarity(
        new_vectors,
        existing_vectors,
    )

    # Find the best existing match for each new embedding.
    best_matches = similarities.max(axis=1)

    # One aggregate score for this existing report.
    return float(best_matches.mean())