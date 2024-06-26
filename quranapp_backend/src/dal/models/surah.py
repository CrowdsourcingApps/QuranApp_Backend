from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from src.dal.database import Base


class Surah(Base):
    __tablename__ = "surahs"
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, nullable=False)
    revelation_type = Column(String, nullable=False)
    title_eng = Column(String, nullable=False)
    title_eng_translation = Column(String, nullable=False)

    ayahs = relationship("Ayah", back_populates="surah")
    surahs_in_mushaf = relationship("SurahInMushaf", back_populates="surah")
