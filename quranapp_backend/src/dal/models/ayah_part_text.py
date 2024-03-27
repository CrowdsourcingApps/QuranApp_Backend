import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.dal.database import Base


class AyahPartText(Base):
    __tablename__ = "ayah_part_texts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(String, nullable=False)

    ayah_parts = relationship("AyahPart", back_populates="text")
    reciter_audios = relationship("ReciterAudio", back_populates="text")
