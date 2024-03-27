import uuid
from types import NoneType

from pydantic import BaseModel

from src.models.ayah_part_marker import AyahPartMarker


class AyahPartBase(BaseModel):
    surah_number: int
    ayah_in_surah_number: int
    part_number: int = 0


class AyahPartSearch(AyahPartBase):
    pass


class AyahPartDetailed(AyahPartBase):
    pass


class AyahPart(BaseModel):
    id: uuid.UUID


class MushafPageAyahPart(AyahPartBase):
    id: uuid.UUID
    text: str | NoneType
    text_id: uuid.UUID | NoneType
    audio_link: str | NoneType
    markers: list[AyahPartMarker]
