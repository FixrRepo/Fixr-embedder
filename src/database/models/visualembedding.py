import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class VisualEmbedding(Base):
    __tablename__ = "visual_embedding"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    report_embedding_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("report_embedding.id"), nullable=False
    )
    embedding = mapped_column("image_embedding", Vector(512), nullable=False)
    report_embedding: Mapped["ReportEmbedding"] = relationship(
        back_populates="visual_embeddings"
    )


from .reportembedding import ReportEmbedding  # noqa: E402,F401
