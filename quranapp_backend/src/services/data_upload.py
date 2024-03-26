import json
import uuid
from tempfile import SpooledTemporaryFile

from sqlalchemy import insert, update
from sqlalchemy.orm import Session

from src.dal.database import Base
from src.dal.models import Ayah, AyahPart, AyahPartText, MushafPage, AyahPartMarker, SurahInMushaf
from src.models.ayah_part_marker import AyahPartMarker as AyahPartMarkerBase
from src.models.mushaf_data import (
    AyahPartsData, AyahPartDetailData, AyahPartMarkerData, PageImagesData, PageImagesDetailData,
    SurahsInMushafData, SurahInMushafDetailData
)
from src.services import (
    surahs as surahs_service,
    ayah_part_texts as ayah_part_texts_service,
    mushaf_pages as mushaf_pages_service,
    ayahs as ayahs_service,
    ayah_parts as ayah_parts_service,
    mushafs as mushafs_service
)


class DataUploadException(Exception):
    pass


class AyahPartsDataUploader:

    def __init__(self, db: Session):
        self.db = db
        self.existing_surahs_numbers = set([surah.id for surah in surahs_service.get_all_surahs(db)])
        self.existing_ayah_parts: dict[str, AyahPart] = dict()
        self.ayah_parts_texts_to_ids_mapping = {
            ayah_part_text.text: ayah_part_text.id
            for ayah_part_text in ayah_part_texts_service.get_all_ayah_part_texts(db)
        }
        self.mushaf_pages_to_ids_mapping = dict()
        self.ayahs_to_ids_mapping = dict()

        self.processed_ayah_part_keys = set()

        self.ayah_parts_to_update = list()
        self.markers_ids_to_delete = list()

    def _fill_ids_for_existing_mushaf_pages(self, mushaf_id: uuid.UUID) -> None:
        for mushaf_page in mushaf_pages_service.get_pages_by_mushaf_id(self.db, mushaf_id):
            self.mushaf_pages_to_ids_mapping[mushaf_page.index] = mushaf_page.id

    def _fill_ids_for_existing_ayahs(self, mushaf_id: uuid.UUID) -> None:
        for ayah in ayahs_service.get_ayahs_by_mushaf_id(self.db, mushaf_id):
            self.ayahs_to_ids_mapping[f"{ayah.surah_number}-{ayah.ayah_in_surah_number}"] = ayah.id

    def _fill_existing_ayah_parts(self, mushaf_id: uuid.UUID) -> None:
        for ayah_part in ayah_parts_service.get_extended_ayah_parts_by_mushaf_id(self.db, mushaf_id):
            ayah_part_key = (f"{ayah_part.ayah.surah_number}-{ayah_part.ayah.ayah_in_surah_number}-"
                             f"{ayah_part.part_number}")
            self.existing_ayah_parts[ayah_part_key] = ayah_part

    def _fill_data_for_existing_objects(self, mushaf_id: uuid.UUID) -> None:
        self._fill_ids_for_existing_ayahs(mushaf_id=mushaf_id)
        self._fill_ids_for_existing_mushaf_pages(mushaf_id=mushaf_id)
        self._fill_existing_ayah_parts(mushaf_id=mushaf_id)

    def _bulk_create_objects(self, objects_data: list[dict], db_model: Base) -> list[Base]:
        """Создает и вовзращает объекты выбранной модели на основе передаваемых данных"""
        db_objects = self.db.scalars(
            insert(db_model).returning(db_model),
            objects_data
        )
        return list(db_objects)

    def _bulk_update_ayah_parts(self) -> None:
        self.db.execute(
            update(AyahPart),
            self.ayah_parts_to_update
        )

    def _delete_outdated_markers(self) -> None:
        self.db.query(AyahPartMarker).filter(AyahPartMarker.id.in_(self.markers_ids_to_delete)).delete()

    def _update_ayah_part(self, ayah_part_key: str, ayah_part_data: AyahPartDetailData, markers_data: list) -> None:
        ayah_part = self.existing_ayah_parts[ayah_part_key]
        ayah_part_id = ayah_part.id
        update_data = dict()

        # Обновление текста
        uploaded_text = ayah_part_data.text
        if uploaded_text is not None:
            if ayah_part.text is None or ayah_part.text.text != uploaded_text:
                text_id = self.ayah_parts_texts_to_ids_mapping[uploaded_text]
                update_data["ayah_part_text_id"] = text_id

        # Обновление страницы
        uploaded_page_number = ayah_part_data.page_number
        if ayah_part.mushaf_page is None or ayah_part.mushaf_page.index != uploaded_page_number:
            mushaf_page_id = self.mushaf_pages_to_ids_mapping[uploaded_page_number]
            update_data["mushaf_page_id"] = mushaf_page_id

        if update_data:
            update_data["id"] = ayah_part_id
            self.ayah_parts_to_update.append(update_data)

        # Обновление маркеров
        uploaded_markers_data = self._form_data_for_ayah_part_markers(ayah_part_data.lines, ayah_part_id)

        uploaded_markers = sorted(
            list(AyahPartMarkerBase(**marker_data) for marker_data in uploaded_markers_data),
            key=lambda x: x.order
        )
        existing_markers = sorted(
            list(AyahPartMarkerBase.model_validate(marker) for marker in ayah_part.markers),
            key=lambda x: x.order
        )

        if uploaded_markers != existing_markers:
            self.markers_ids_to_delete.extend([marker.id for marker in ayah_part.markers])
            markers_data.extend(uploaded_markers_data)

    def _form_data_for_ayah_part_markers(
            self, markers: list[list[AyahPartMarkerData]], ayah_part_id: uuid.UUID
    ) -> list[dict]:
        markers_data = list()
        order = 0
        for particular_line_markers in markers:
            for ind, marker in enumerate(particular_line_markers):
                is_new_line = True if ind == 0 else False
                markers_data.append({
                    "order": order, "is_new_line": is_new_line, "ayah_part_id": ayah_part_id,
                    "x": marker.x, "y1": marker.y1, "y2": marker.y2,
                })
                order += 1
        return markers_data

    def _validate_surah_number(self, surah_number: int):
        if surah_number not in self.existing_surahs_numbers:
            raise DataUploadException(f"Surah with number '{surah_number}' does not exist")

    def _create_objects_from_ayah_parts_data(self, mushaf_id: uuid.UUID, data: list[AyahPartDetailData]) -> None:
        ayahs_data = list()
        ayah_part_texts_data = list()
        mushaf_pages_data = list()
        ayah_parts_data = list()
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

            if ayah_part_key in self.processed_ayah_part_keys:
                raise DataUploadException(
                    f"Data is duplicated for the following ayah part: "
                    f"surah number = {surah_number}, ayah number = {ayah_in_surah_number}, "
                    f"part number = {ayah_part_number}"
                )

            self.processed_ayah_part_keys.add(ayah_part_key)

            if ayah_part_key in self.existing_ayah_parts:
                self._update_ayah_part(ayah_part_key, uploaded_ayah_part_data, markers_data)

            else:
                ayah_part_id = uuid.uuid4()
                ayah_parts_data.append({
                    "id": ayah_part_id, "part_number": ayah_part_number, "ayah_id": ayah_id,
                    "ayah_part_text_id": ayah_part_text_id, "mushaf_page_id": mushaf_page_id
                })

                markers_data.extend(
                    self._form_data_for_ayah_part_markers(uploaded_ayah_part_data.lines, ayah_part_id)
                )

        if ayahs_data:
            self._bulk_create_objects(ayahs_data, Ayah)

        if ayah_part_texts_data:
            self._bulk_create_objects(ayah_part_texts_data, AyahPartText)

        if mushaf_pages_data:
            self._bulk_create_objects(mushaf_pages_data, MushafPage)

        if ayah_parts_data:
            self._bulk_create_objects(ayah_parts_data, AyahPart)

        if self.markers_ids_to_delete:
            self._delete_outdated_markers()

        if markers_data:
            self._bulk_create_objects(markers_data, AyahPartMarker)

        self._bulk_update_ayah_parts()

        self.db.commit()

    def save_data_from_ayah_parts_file(self, file: SpooledTemporaryFile) -> None:
        try:
            uploaded_data = json.load(file)
        except json.JSONDecodeError as e:
            raise DataUploadException(f"Error in file formatting - not valid json. Details: {e.args}")

        if not isinstance(uploaded_data, dict):
            raise DataUploadException("Unexpected file structure. Expected: {...}")

        # ValidationError, который здесь может возникнуть, обрабатывается в самой функции эндпоинта
        validated_ayah_parts_data = AyahPartsData(**uploaded_data)

        mushaf = mushafs_service.get_or_create_mushaf(
            self.db, validated_ayah_parts_data.riwayah, validated_ayah_parts_data.publisher
        )

        self._fill_data_for_existing_objects(mushaf_id=mushaf.id)

        self._create_objects_from_ayah_parts_data(mushaf_id=mushaf.id, data=validated_ayah_parts_data.ayah_parts_data)


class PageImagesDataUploader:

    def __init__(self, db: Session):
        self.db = db
        self.existing_mushaf_pages: dict[int, MushafPage] = dict()

        self.processed_page_numbers = set()

        self.mushaf_pages_to_update = list()

    def _fill_existing_mushaf_pages(self, mushaf_id: uuid.UUID) -> None:
        for mushaf_page in mushaf_pages_service.get_pages_by_mushaf_id(self.db, mushaf_id):
            self.existing_mushaf_pages[mushaf_page.index] = mushaf_page

    def _bulk_create_objects(self, objects_data: list[dict], db_model: Base) -> list[Base]:
        db_objects = self.db.scalars(
            insert(db_model).returning(db_model),
            objects_data
        )
        return list(db_objects)

    def _bulk_update_mushaf_pages(self) -> None:
        self.db.execute(update(MushafPage), self.mushaf_pages_to_update)

    def _update_mushaf_page(self, page_number: int, uploaded_page_data: PageImagesDetailData) -> None:
        page = self.existing_mushaf_pages[page_number]
        update_data = dict()
        if page.light_mode_link != uploaded_page_data.light_mode_link:
            update_data["light_mode_link"] = uploaded_page_data.light_mode_link
        if page.dark_mode_link != uploaded_page_data.dark_mode_link:
            update_data["dark_mode_link"] = uploaded_page_data.dark_mode_link
        if update_data:
            update_data["id"] = page.id
            self.mushaf_pages_to_update.append(update_data)

    def _create_objects_from_page_images_data(self, mushaf_id: uuid.UUID, data: list[PageImagesDetailData]) -> None:
        mushaf_pages_data = list()

        for uploaded_page_data in data:
            page_number = uploaded_page_data.page_number

            if page_number in self.processed_page_numbers:
                raise DataUploadException(f"Data is duplicated for the following mushaf page: {page_number}")

            self.processed_page_numbers.add(page_number)

            if page_number in self.existing_mushaf_pages:
                self._update_mushaf_page(page_number, uploaded_page_data)
            else:
                mushaf_pages_data.append({
                    "index": page_number,
                    "mushaf_id": mushaf_id,
                    "light_mode_link": uploaded_page_data.light_mode_link,
                    "dark_mode_link": uploaded_page_data.dark_mode_link
                })

        if mushaf_pages_data:
            self._bulk_create_objects(mushaf_pages_data, MushafPage)

        self._bulk_update_mushaf_pages()

        self.db.commit()

    def save_data_from_page_images_file(self, file: SpooledTemporaryFile) -> None:
        try:
            uploaded_data = json.load(file)
        except json.JSONDecodeError as e:
            raise DataUploadException(f"Error in file formatting - not valid json. Details: {e.args}")

        if not isinstance(uploaded_data, dict):
            raise DataUploadException("Unexpected file structure. Expected: {...}")

        validated_page_images_data = PageImagesData(**uploaded_data)

        mushaf = mushafs_service.get_or_create_mushaf(
            self.db, validated_page_images_data.riwayah, validated_page_images_data.publisher
        )

        self._fill_existing_mushaf_pages(mushaf_id=mushaf.id)

        self._create_objects_from_page_images_data(mushaf_id=mushaf.id, data=validated_page_images_data.pages)


class SurahsInMushafDataUploader:
    def __init__(self, db: Session):
        self.db = db
        self.existing_surahs_numbers = set([surah.id for surah in surahs_service.get_all_surahs(db)])
        self.existing_surahs_in_mushaf: dict[int, SurahInMushaf] = dict()
        self.mushaf_pages_to_ids_mapping = dict()

        self.processed_surahs = set()

    def _fill_ids_for_existing_mushaf_pages(self, mushaf_id: uuid.UUID) -> None:
        for mushaf_page in mushaf_pages_service.get_pages_by_mushaf_id(self.db, mushaf_id):
            self.mushaf_pages_to_ids_mapping[mushaf_page.index] = mushaf_page.id

    def _fill_existing_surahs_in_mushaf(self, mushaf_id: uuid.UUID) -> None:
        for surah_in_mushaf in surahs_service.get_surahs_in_mushaf(self.db, mushaf_id):
            self.existing_surahs_in_mushaf[surah_in_mushaf.surah_number] = surah_in_mushaf

    def _fill_data_for_existing_objects(self, mushaf_id: uuid.UUID) -> None:
        self._fill_ids_for_existing_mushaf_pages(mushaf_id=mushaf_id)
        self._fill_existing_surahs_in_mushaf(mushaf_id=mushaf_id)

    def _bulk_create_objects(self, objects_data: list[dict], db_model: Base) -> list[Base]:
        db_objects = self.db.scalars(
            insert(db_model).returning(db_model),
            objects_data
        )
        return list(db_objects)

    def _validate_surah_number(self, surah_number: int):
        if surah_number not in self.existing_surahs_numbers:
            raise DataUploadException(f"Surah with number '{surah_number}' does not exist")

    def _update_surah_in_mushaf(self, surah_number: int, page_id: uuid.UUID) -> None:
        surah_in_mushaf = self.existing_surahs_in_mushaf[surah_number]
        if surah_in_mushaf.first_page_id != page_id:
            surah_in_mushaf.first_page_id = page_id

    def _create_objects_from_surahs_in_mushaf_data(
            self, mushaf_id: uuid.UUID, data: list[SurahInMushafDetailData]
    ) -> None:
        surahs_in_mushaf_data = list()
        mushaf_pages_data = list()

        for uploaded_surah_in_mushaf_data in data:
            surah_number = uploaded_surah_in_mushaf_data.surah_number

            if surah_number in self.processed_surahs:
                raise DataUploadException(f"Data is duplicated for the following surah: {surah_number}")
            self.processed_surahs.add(surah_number)

            self._validate_surah_number(surah_number)

            page_number = uploaded_surah_in_mushaf_data.page_number
            if page_number in self.mushaf_pages_to_ids_mapping:
                mushaf_page_id = self.mushaf_pages_to_ids_mapping[page_number]
            else:
                mushaf_page_id = uuid.uuid4()
                mushaf_pages_data.append({"id": mushaf_page_id, "index": page_number, "mushaf_id": mushaf_id})
                self.mushaf_pages_to_ids_mapping[page_number] = mushaf_page_id

            if surah_number in self.existing_surahs_in_mushaf:
                self._update_surah_in_mushaf(surah_number, mushaf_page_id)
            else:
                surahs_in_mushaf_data.append({
                    "first_page_id": mushaf_page_id,
                    "surah_number": surah_number
                })

        if mushaf_pages_data:
            self._bulk_create_objects(mushaf_pages_data, MushafPage)

        if surahs_in_mushaf_data:
            self._bulk_create_objects(surahs_in_mushaf_data, SurahInMushaf)

        self.db.commit()

    def save_data_from_surahs_in_mushaf_file(self, file: SpooledTemporaryFile) -> None:
        try:
            uploaded_data = json.load(file)
        except json.JSONDecodeError as e:
            raise DataUploadException(f"Error in file formatting - not valid json. Details: {e.args}")

        if not isinstance(uploaded_data, dict):
            raise DataUploadException("Unexpected file structure. Expected: {...}")

        validated_surahs_in_mushaf_data = SurahsInMushafData(**uploaded_data)

        mushaf = mushafs_service.get_or_create_mushaf(
            self.db, validated_surahs_in_mushaf_data.riwayah, validated_surahs_in_mushaf_data.publisher
        )

        self._fill_data_for_existing_objects(mushaf_id=mushaf.id)

        self._create_objects_from_surahs_in_mushaf_data(
            mushaf_id=mushaf.id, data=validated_surahs_in_mushaf_data.surahs
        )
