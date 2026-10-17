# models/report_embedding.py

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography
from pgvector.sqlalchemy import Vector

from .base import Base

class ReportEmbedding(Base):
    __tablename__ = "report_embedding"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )


    coordinate = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    text_embedding = mapped_column(
        Vector(512), 
        nullable=True,
    )

    visual_embeddings: Mapped[list["visualEmbedding"]] = relationship(
        back_populates="report_embedding",
    )

    status: Mapped[str]
