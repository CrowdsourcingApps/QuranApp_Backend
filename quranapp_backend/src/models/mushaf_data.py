from pydantic import BaseModel, Field

from src.dal.enums import RiwayahEnum, PublisherEnum


class AyahPartMarkerData(BaseModel):
    x: int
    y1: int
    y2: int


class AyahPartDetailData(BaseModel):
    page_number: int
    surah_number: int
    ayah_number: int
    part_number: int = 0
    text: str | None = None
    lines: list[list[AyahPartMarkerData]]


class AyahPartsData(BaseModel):
    riwayah: RiwayahEnum
    publisher: PublisherEnum
    ayah_parts_data: list[AyahPartDetailData] = Field(alias="ayahParts")


class PageImagesDetailData(BaseModel):
    page_number: int
    light_mode_link: str
    dark_mode_link: str


class PageImagesData(BaseModel):
    riwayah: RiwayahEnum
    publisher: PublisherEnum
    pages: list[PageImagesDetailData]


class SurahInMushafDetailData(BaseModel):
    surah_number: int
    page_number: int


class SurahsInMushafData(BaseModel):
    riwayah: RiwayahEnum
    publisher: PublisherEnum
    surahs: list[SurahInMushafDetailData]
