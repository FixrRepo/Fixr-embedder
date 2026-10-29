import uuid

from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

from .base import Base

class ReportEmbedding(Base):
    __tablename__ = "report_embedding"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    coordinate = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=False
    )
    text_embedding = mapped_column(Vector(512), nullable=True)
    visual_embeddings: Mapped[list["VisualEmbedding"]] = relationship(
        back_populates="report_embedding",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


from .visualembedding import VisualEmbedding  # noqa: E402,F401
