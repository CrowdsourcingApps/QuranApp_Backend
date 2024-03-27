import uuid

from sqlalchemy.orm import Session, joinedload, contains_eager

from src.dal.models import MushafPage, Ayah, AyahPart, AyahPartText, ReciterAudio
from src.mappers import ayah_part_mapper
from src.models import MushafPageDetails


def get_pages_by_mushaf_id(db: Session, mushaf_id: uuid.UUID) -> list[MushafPage]:
    return db.query(MushafPage).filter_by(mushaf_id=mushaf_id).all()


def get_ayah_parts_and_markers_by_page_id(db: Session, page_id: uuid.UUID) -> MushafPageDetails:
    # contains_eager использую, чтобы иметь возможность фильтровать после JOIN'а, и при этом иметь доступ
    # к атрибутам Aayh. Документация: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#routing-explicit-joins-statements-into-eagerly-loaded-collections
    ayah_parts = db.query(AyahPart).filter_by(mushaf_page_id=page_id).join(Ayah, Ayah.id == AyahPart.ayah_id).options(
        contains_eager(AyahPart.ayah).joinedload(Ayah.mushaf),
        joinedload(AyahPart.markers),
        joinedload(AyahPart.text).joinedload(AyahPartText.reciter_audios).joinedload(ReciterAudio.reciter)
    ).order_by(Ayah.surah_number, Ayah.ayah_in_surah_number).all()

    return ayah_part_mapper.map_to_page_details(page_id=page_id, ayah_parts=ayah_parts)
