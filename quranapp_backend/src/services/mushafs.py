import json
import uuid
from tempfile import SpooledTemporaryFile

from sqlalchemy import insert
from sqlalchemy.orm import Session

from src.dal.database import Base
from src.dal.enums import RiwayahEnum, PublisherEnum
from src.dal.models import Mushaf, Ayah, AyahPart, AyahPartText, MushafPage, AyahPartMarker
from src.models.mushaf_data import MushafData, AyahPartData, AyahPartMarkerData
from src.services import (
    surahs as surahs_service,
    ayah_part_texts as ayah_part_texts_service,
    mushaf_pages as mushaf_pages_service,
    ayahs as ayahs_service,
    ayah_parts as ayah_parts_service
)


def create_mushaf(db: Session, riwayah: RiwayahEnum, publisher: PublisherEnum) -> Mushaf:
    db_mushaf = Mushaf(riwayah=riwayah, publisher=publisher)
    db.add(db_mushaf)
    db.commit()
    db.refresh(db_mushaf)
    return db_mushaf


def get_mushaf_if_exists(db: Session, riwayah: RiwayahEnum, publisher: PublisherEnum) -> Mushaf | None:
    return db.query(Mushaf).filter_by(riwayah=riwayah, publisher=publisher).first()


class DataUploadException(Exception):
    pass


class MushafDataUploader:

    def __init__(self, db: Session):
        self.db = db
        self.existing_surahs_numbers = set([surah.id for surah in surahs_service.get_all_surahs(db)])
        self.existing_ayah_parts = set()
        self.ayah_parts_texts_to_ids_mapping = {
            ayah_part_text.text: ayah_part_text.id
            for ayah_part_text in ayah_part_texts_service.get_all_ayah_part_texts(db)
        }
        self.mushaf_pages_to_ids_mapping = dict()
        self.ayahs_to_ids_mapping = dict()

    def _fill_ids_for_existing_mushaf_pages(self, mushaf_id: uuid.UUID) -> None:
        for mushaf_page in mushaf_pages_service.get_pages_by_mushaf_id(self.db, mushaf_id):
            self.mushaf_pages_to_ids_mapping[mushaf_page.index] = mushaf_page.id

    def _fill_ids_for_existing_ayahs(self, mushaf_id: uuid.UUID) -> None:
        for ayah in ayahs_service.get_ayahs_by_mushaf_id(self.db, mushaf_id):
            self.ayahs_to_ids_mapping[f"{ayah.surah_number}-{ayah.ayah_in_surah_number}"] = ayah.id

    def _fill_ids_for_existing_ayah_parts(self, mushaf_id: uuid.UUID) -> None:
        for ayah_part in ayah_parts_service.get_extended_ayah_parts_by_mushaf_id(self.db, mushaf_id):
            self.existing_ayah_parts.add(
                f"{ayah_part.ayah.surah_number}-{ayah_part.ayah.ayah_in_surah_number}-{ayah_part.part_number}"
            )

    def _fill_ids_for_existing_objects(self, mushaf_id: uuid.UUID) -> None:
        self._fill_ids_for_existing_ayahs(mushaf_id=mushaf_id)
        self._fill_ids_for_existing_mushaf_pages(mushaf_id=mushaf_id)
        self._fill_ids_for_existing_ayah_parts(mushaf_id=mushaf_id)

    def _bulk_create_objects(self, objects_data: list[dict], db_model: Base) -> list[Base]:
        """Создает и вовзращает объекты выбранной модели на основе передаваемых данных"""
        db_objects = self.db.scalars(
            insert(db_model).returning(db_model),
            objects_data
        )
        return list(db_objects)

    def _update_ayah_part(self, ayah_part_key: str, ayah_part_data: AyahPartData):
        pass

    def _add_data_for_ayah_markers(
            self, markers: list[list[AyahPartMarkerData]], ayah_part_id: uuid.UUID, markers_data: list
    ):
        order = 0
        for particular_line_markers in markers:
            for ind, marker in enumerate(particular_line_markers):
                is_new_line = True if ind == 0 else False
                markers_data.append({
                    "order": order, "is_new_line": is_new_line, "ayah_part_id": ayah_part_id,
                    "x": marker.x, "y1": marker.y1, "y2": marker.y2,
                })
                order += 1

    def _validate_surah_number(self, surah_number: int):
        if surah_number not in self.existing_surahs_numbers:
            raise DataUploadException(f"Surah with number '{surah_number}' does not exist")

    def _create_objects_from_mushaf_data(self, mushaf_id: uuid.UUID, data: list[AyahPartData]) -> None:
        ayahs_data = list()
        ayah_part_texts_data = list()
        mushaf_pages_data = list()
        ayah_parts_data = dict()
        markers_data = list()

        for uploaded_ayah_part_data in data:

            surah_number, ayah_in_surah_number = uploaded_ayah_part_data.surah_number, uploaded_ayah_part_data.ayah_number

            # Добавление данных по Ayah, получение id Ayah
            ayah_key = f"{surah_number}-{ayah_in_surah_number}"
            if ayah_key in self.ayahs_to_ids_mapping:
                ayah_id = self.ayahs_to_ids_mapping[ayah_key]
            else:
                self._validate_surah_number(surah_number)
                ayah_id = uuid.uuid4()
                ayahs_data.append({
                    "id": ayah_id, "mushaf_id": mushaf_id, "surah_number": surah_number,
                    "ayah_in_surah_number": ayah_in_surah_number
                })
                self.ayahs_to_ids_mapping[ayah_key] = ayah_id

            # Добавление данных по AyahPartText, получение id AyahPartText
            ayah_part_text = uploaded_ayah_part_data.text
            ayah_part_text_id = None

            if ayah_part_text is not None:
                if ayah_part_text in self.ayah_parts_texts_to_ids_mapping:
                    ayah_part_text_id = self.ayah_parts_texts_to_ids_mapping[ayah_part_text]
                else:
                    ayah_part_text_id = uuid.uuid4()
                    ayah_part_texts_data.append({"id": ayah_part_text_id, "text": ayah_part_text})
                    self.ayah_parts_texts_to_ids_mapping[ayah_part_text] = ayah_part_text_id

            # Добавление данных по MushafPage, получение id MushafPage
            page_number = uploaded_ayah_part_data.page_number
            if page_number in self.mushaf_pages_to_ids_mapping:
                mushaf_page_id = self.mushaf_pages_to_ids_mapping[page_number]
            else:
                mushaf_page_id = uuid.uuid4()
                mushaf_pages_data.append({"id": mushaf_page_id, "index": page_number, "mushaf_id": mushaf_id})
                self.mushaf_pages_to_ids_mapping[page_number] = mushaf_page_id

            # Добавление данных по AyahPart и AyahPartMarkers | обновление AyahPart
            ayah_part_number = uploaded_ayah_part_data.part_number
            ayah_part_key = f"{ayah_key}-{ayah_part_number}"

            if ayah_part_key in self.existing_ayah_parts:
                self._update_ayah_part(ayah_part_key, uploaded_ayah_part_data)

            else:
                if ayah_part_key in ayah_parts_data:
                    raise DataUploadException(
                        f"Data is duplicated for the following ayah part: "
                        f"surah number = {surah_number}, ayah number = {ayah_in_surah_number},"
                        f"part number = {ayah_part_number}"
                    )

                ayah_part_id = uuid.uuid4()
                ayah_parts_data[ayah_part_key] = {
                    "id": ayah_part_id, "part_number": ayah_part_number, "ayah_id": ayah_id,
                    "ayah_part_text_id": ayah_part_text_id, "mushaf_page_id": mushaf_page_id
                }

                self._add_data_for_ayah_markers(uploaded_ayah_part_data.lines, ayah_part_id, markers_data)

        if ayahs_data:
            self._bulk_create_objects(ayahs_data, Ayah)

        if ayah_part_texts_data:
            self._bulk_create_objects(ayah_part_texts_data, AyahPartText)

        if mushaf_pages_data:
            self._bulk_create_objects(mushaf_pages_data, MushafPage)

        if ayah_parts_data:
            self._bulk_create_objects(list(ayah_parts_data.values()), AyahPart)

        if markers_data:
            self._bulk_create_objects(markers_data, AyahPartMarker)

        self.db.commit()

    def save_data_from_mushaf_file(self, file: SpooledTemporaryFile):
        try:
            mushaf_data = json.load(file)
        except json.JSONDecodeError as e:
            raise DataUploadException(f"Error in file formatting - not valid json. Details: {e.args}")

        if not isinstance(mushaf_data, dict):
            raise DataUploadException("Unexpected file structure. Expected: {...}")

        # ValidationError, который здесь может возникнуть, обрабатывается в самой функции эндпоинта
        validated_mushaf_data = MushafData(**mushaf_data)

        mushaf = get_mushaf_if_exists(self.db, validated_mushaf_data.riwayah, validated_mushaf_data.publisher)
        if not mushaf:
            mushaf = create_mushaf(self.db, validated_mushaf_data.riwayah, validated_mushaf_data.publisher)

        self._fill_ids_for_existing_objects(mushaf_id=mushaf.id)

        self._create_objects_from_mushaf_data(mushaf_id=mushaf.id, data=validated_mushaf_data.ayah_parts_data)