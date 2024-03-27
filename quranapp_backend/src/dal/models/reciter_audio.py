from sqlalchemy import Column, ForeignKey, PrimaryKeyConstraint, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.dal.database import Base


class ReciterAudio(Base):
    __tablename__ = 'reciter_audios'
    reciter_id = Column(UUID(as_uuid=True), ForeignKey('reciters.id'), nullable=False)
    ayah_part_text_id = Column(UUID(as_uuid=True), ForeignKey('ayah_part_texts.id'), nullable=False)
    audio_link = Column(String, nullable=False)

    text = relationship("AyahPartText", back_populates="reciter_audios")
    reciter = relationship("Reciter", back_populates="audios")

    __table_args__ = (
        PrimaryKeyConstraint('reciter_id', 'ayah_part_text_id'),
        Index('ix_ayah_part_text_id', 'ayah_part_text_id')
    )
