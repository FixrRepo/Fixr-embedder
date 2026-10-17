import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..models.reportembedding import ReportEmbedding
from ..database import SessionLocal
import math 

def compute_cadidate_scores(incomingEmbedding: ReportEmbedding):
    session = SessionLocal()
    candidates = find_report_within_search_radius(session, incomingEmbedding.coordinate, 50 )

    ranked_candidates = []

    for candidate in candidates:
        existing_vectors = [np.ndarray(embedding, dtype=np.float32) for embedding in candidate.visual_embeddings]

        visual_score = calculate_visual_score(incomingEmbedding.visual_embeddings, existing_vectors)
        text_score = calculate_text_score(incomingEmbedding.text_embedding, candidate.text_embedding)
        distance = func.ST_Distance(candidate.coordinate, incomingEmbedding.coordinate)
        distance_score = math.exp(math.pow())


def find_report_within_search_radius(session, incomingCoordinate, search_radius)->list[ReportEmbedding]:
    statement = (select(ReportEmbedding)
                 .where(
                     func.ST_DWithin(ReportEmbedding.coordinate, incomingCoordinate, search_radius)
                 ).options(
                     selectinload(ReportEmbedding.visual_embeddings)
                 ))
    return session.scalars(statement).all()

def calculate_text_score(new_embedding: np.array, existing_embedding: np.array):
    similarities = cosine_similarity(new_embedding, existing_embedding)
    return float(similarities.flatten())


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