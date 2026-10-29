from uuid import UUID

import numpy as np
import math
from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.orm import aliased, selectinload

from ...embedding.similarity import calculate_visual_score
from ..database import SessionLocal
from ..models.reportembedding import ReportEmbedding
from ...config import  settings

def _vectors(visual_embeddings) -> list[np.ndarray]:
    """Extract raw vectors at the ORM boundary for the pure scoring function."""
    return [
        np.asarray(item.embedding, dtype=np.float32).reshape(-1)
        for item in visual_embeddings
    ]


def find_report_within_search_radius(
    session, incoming_id: UUID, search_radius: float
) -> list[tuple[ReportEmbedding, float]]:
    """Fetch nearby report embeddings and geography distances in metres."""
    incoming_report = aliased(ReportEmbedding)
    coordinate_geography = cast(ReportEmbedding.coordinate, Geography(srid=4326))
    incoming_geography = cast(incoming_report.coordinate, Geography(srid=4326))
    distance = func.ST_Distance(coordinate_geography, incoming_geography)
    statement = (
        select(ReportEmbedding, distance.label("distance_meters"))
        .join(incoming_report, incoming_report.id == incoming_id)
        .where(func.ST_DWithin(coordinate_geography, incoming_geography, search_radius))
        .where(ReportEmbedding.id != incoming_id)
        .options(selectinload(ReportEmbedding.visual_embeddings))
    )
    return [(row[0], float(row[1])) for row in session.execute(statement).all()]


def compute_candidate_scores(
    incoming_report_id: str, search_radius: float = 50, top_n: int = 5
) -> list[dict]:
    """Rank nearby reports by visual evidence; geography only filters candidates."""
    if search_radius < 0:
        raise ValueError("search_radius must not be negative")
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    with SessionLocal() as session:
        incoming = session.get(ReportEmbedding, UUID(str(incoming_report_id)))
        if incoming is None:
            raise LookupError(f"Report embedding not found for report {incoming_report_id}")
        incoming_vectors = _vectors(incoming.visual_embeddings)
        candidates = find_report_within_search_radius(
            session,
            incoming.id,
            search_radius,
        )

        scored = []
        for candidate, distance_meters in candidates:
            visual_score = calculate_visual_score(
                incoming_vectors, _vectors(candidate.visual_embeddings)
            )
            if visual_score is None:
                continue
            scored.append(
                {
                    "reportId": str(candidate.id),
                    "visualScore": visual_score,
                    "distanceMeters": distance_meters,
                    "distanceScore": exponentialDecay(distance_meters),
                    "similarityScore": computeSimilarityScore(visual_score, distance_meters)
                }
            )

    scored.sort(key=lambda item: item["similarityScore"], reverse=True)
    ranked = scored[:top_n]
    for rank, candidate in enumerate(ranked, start=1):
        candidate["rank"] = rank
    return ranked

def computeSimilarityScore(visualScore: float, distance_m: float):
    visualScoreW = visualScore* settings.VISUAL_SIMILARITY_SCORE_WEIGHT
    distanceScoreW = exponentialDecay(distance_m) * settings.DISTANCE_SIMILARITY_SCORE_WEIGHT

    return visualScoreW + distanceScoreW

def exponentialDecay(distance_meters:float):
    return math.pow(math.exp(-(distance_meters/settings.EXPONENTIAL_DECAY_RATE)), 2)
