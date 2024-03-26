import os

import pytest
from sqlalchemy.orm import joinedload

from src.services import data_upload as data_upload_service
from src.dal.models import AyahPart, AyahPartMarker, AyahPartText, Ayah, MushafPage, Surah, SurahInMushaf


ayah_parts_data_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_data", "ayah_parts_upload")
page_images_data_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_data", "page_images_upload")
surahs_in_mushaf_data_directory = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "test_data", "surahs_in_mushaf_upload"
)


class TestAyahPartsDataUploader:
    def test_data_upload(self, db_session):
        ayahs_count = db_session.query(Ayah).count()
        ayah_parts_count = db_session.query(AyahPart).count()
        ayah_part_texts_count = db_session.query(AyahPartText).count()
        mushaf_pages_count = db_session.query(MushafPage).count()
        ayah_part_markers_count = db_session.query(AyahPartMarker).count()

        ayah_parts_data_uploader = data_upload_service.AyahPartsDataUploader(db=db_session)
        with open(os.path.join(ayah_parts_data_directory, "ayah_parts_page_5000.json")) as f:
            ayah_parts_data_uploader.save_data_from_ayah_parts_file(f)

        new_ayahs_count = db_session.query(Ayah).count()
        new_ayah_parts_count = db_session.query(AyahPart).count()
        new_ayah_part_texts_count = db_session.query(AyahPartText).count()
        new_mushaf_pages_count = db_session.query(MushafPage).count()
        new_ayah_part_markers_count = db_session.query(AyahPartMarker).count()

        assert new_ayahs_count == ayahs_count + 8
        assert new_ayah_parts_count == ayah_parts_count + 9
        assert new_ayah_part_texts_count == ayah_part_texts_count + 3  # 3 new unique texts
        assert new_mushaf_pages_count == mushaf_pages_count + 1
        assert new_ayah_part_markers_count > ayah_part_markers_count

    def test_data_upload_same_data(self, db_session):
        ayah_parts_count = db_session.query(AyahPart).count()
        mushaf_pages_count = db_session.query(MushafPage).count()
        ayah_part_markers_count = db_session.query(AyahPartMarker).count()

        ayah_parts_data_uploader = data_upload_service.AyahPartsDataUploader(db=db_session)
        with open(os.path.join(ayah_parts_data_directory, "ayah_parts_page_5000.json")) as f:
            ayah_parts_data_uploader.save_data_from_ayah_parts_file(f)

        new_ayah_parts_count = db_session.query(AyahPart).count()
        new_mushaf_pages_count = db_session.query(MushafPage).count()
        new_ayah_part_markers_count = db_session.query(AyahPartMarker).count()

        assert new_ayah_parts_count == ayah_parts_count
        assert new_mushaf_pages_count == mushaf_pages_count
        assert new_ayah_part_markers_count == ayah_part_markers_count

    def test_ayah_parts_update(self, db_session):
        ayah_part_1 = db_session.query(AyahPart).filter(AyahPart.ayah.has(ayah_in_surah_number=1003)).options(
            joinedload(AyahPart.markers)
        ).first()
        ayah_part_2 = db_session.query(AyahPart).filter(AyahPart.ayah.has(ayah_in_surah_number=1005)).options(
            joinedload(AyahPart.text)
        ).first()

        assert len(ayah_part_1.markers) == 0
        assert ayah_part_2.text.text == "Test text data upload"

        ayah_parts_data_uploader = data_upload_service.AyahPartsDataUploader(db=db_session)
        with open(os.path.join(ayah_parts_data_directory, "ayah_parts_page_5000_updated.json")) as f:
            ayah_parts_data_uploader.save_data_from_ayah_parts_file(f)

        updated_ayah_part_1 = db_session.query(AyahPart).filter(AyahPart.ayah.has(ayah_in_surah_number=1003)).options(
            joinedload(AyahPart.markers)
        ).first()
        updated_ayah_part_2 = db_session.query(AyahPart).filter(AyahPart.ayah.has(ayah_in_surah_number=1005)).options(
            joinedload(AyahPart.text)
        ).first()

        assert len(updated_ayah_part_1.markers) == 5
        assert updated_ayah_part_2.text.text == "Test text data upload. Updated text"

    def test_data_upload_unexisting_surah(self, db_session):
        ayah_parts_count = db_session.query(AyahPart).count()
        ayah_part_texts_count = db_session.query(AyahPartText).count()

        ayah_parts_data_uploader = data_upload_service.AyahPartsDataUploader(db=db_session)
        with open(os.path.join(ayah_parts_data_directory, "ayah_parts_page_5000_unexisting_surah.json")) as f:
            with pytest.raises(data_upload_service.DataUploadException):
                ayah_parts_data_uploader.save_data_from_ayah_parts_file(f)

        new_ayah_parts_count = db_session.query(AyahPart).count()
        new_ayah_part_texts_count = db_session.query(AyahPartText).count()

        # No data should be saved if there is an error during data upload
        assert new_ayah_parts_count == ayah_parts_count
        assert new_ayah_part_texts_count == ayah_part_texts_count

    def test_data_upload_invalid_json(self, db_session):
        ayah_parts_data_uploader = data_upload_service.AyahPartsDataUploader(db=db_session)
        with open(os.path.join(ayah_parts_data_directory, "ayah_parts_json_invalid.json")) as f:
            with pytest.raises(data_upload_service.DataUploadException):
                ayah_parts_data_uploader.save_data_from_ayah_parts_file(f)


class TestPageImagesDataUploader:
    def test_data_upload(self, db_session, mushaf):
        page_1 = db_session.query(MushafPage).filter_by(index=5000).first()
        if not page_1:
            page_1 = MushafPage(index=5000, mushaf_id=mushaf.id)
            db_session.add(page_1)
            db_session.commit()
            db_session.refresh(page_1)

        assert page_1.light_mode_link is None and page_1.dark_mode_link is None

        page_images_data_uploader = data_upload_service.PageImagesDataUploader(db=db_session)
        with open(os.path.join(page_images_data_directory, "page_images_pages_5000_5001.json")) as f:
            page_images_data_uploader.save_data_from_page_images_file(f)

        db_session.refresh(page_1)
        assert page_1.light_mode_link is not None and page_1.dark_mode_link is not None

        # New page, created after data upload
        page_2 = db_session.query(MushafPage).filter_by(index=5000).first()
        assert page_2 is not None
        assert page_2.light_mode_link is not None and page_2.dark_mode_link is not None


class TestSurahsInMushafDataUploader:
    def create_test_surahs(self, db_session):
        surah_1 = Surah(id=500, title="Test_1", revelation_type="Test_1", title_eng="Test_1", title_eng_translation="Test_1")
        surah_2 = Surah(id=501, title="Test_2", revelation_type="Test_2", title_eng="Test_2", title_eng_translation="Test_2")
        db_session.add(surah_1)
        db_session.add(surah_2)
        db_session.commit()

    def test_data_upload(self, db_session):
        self.create_test_surahs(db_session)

        mushaf_pages_count = db_session.query(MushafPage).count()

        surahs_in_mushaf_data_uploader = data_upload_service.SurahsInMushafDataUploader(db=db_session)
        with open(os.path.join(surahs_in_mushaf_data_directory, "surahs.json")) as f:
            surahs_in_mushaf_data_uploader.save_data_from_surahs_in_mushaf_file(f)

        new_mushaf_pages_count = db_session.query(MushafPage).count()

        # If first pages of surahs were not in DB - they should be created
        assert new_mushaf_pages_count == mushaf_pages_count + 2

        surahs_in_mushaf = db_session.query(SurahInMushaf).filter(
            SurahInMushaf.surah_number >= 500
        ).order_by(SurahInMushaf.surah_number).all()

        surah_in_mushaf_1, surah_in_mushaf_2 = surahs_in_mushaf
        assert surah_in_mushaf_1.surah_number == 500
        assert surah_in_mushaf_1.mushaf_page.index == 6000

        assert surah_in_mushaf_2.surah_number == 501
        assert surah_in_mushaf_2.mushaf_page.index == 6001

    def test_surah_in_mushaf_update(self, db_session):
        surah_in_mushaf = db_session.query(SurahInMushaf).filter(
            SurahInMushaf.surah_number == 500
        ).first()

        assert surah_in_mushaf.mushaf_page.index == 6000

        surahs_in_mushaf_data_uploader = data_upload_service.SurahsInMushafDataUploader(db=db_session)
        with open(os.path.join(surahs_in_mushaf_data_directory, "surahs_updated.json")) as f:
            surahs_in_mushaf_data_uploader.save_data_from_surahs_in_mushaf_file(f)

        updated_surah_in_mushaf = db_session.query(SurahInMushaf).filter(
            SurahInMushaf.surah_number == 500
        ).first()
        assert updated_surah_in_mushaf.mushaf_page.index == 6005

    def test_surah_duplicate_data(self, db_session):
        """Check that if data is duplicated for surah, then error is raised and no data is saved"""
        mushaf_pages_count = db_session.query(MushafPage).count()

        surahs_in_mushaf_data_uploader = data_upload_service.SurahsInMushafDataUploader(db=db_session)
        with open(os.path.join(surahs_in_mushaf_data_directory, "surahs_duplicates.json")) as f:
            with pytest.raises(data_upload_service.DataUploadException):
                surahs_in_mushaf_data_uploader.save_data_from_surahs_in_mushaf_file(f)

        new_mushaf_pages_count = db_session.query(MushafPage).count()
        assert new_mushaf_pages_count == mushaf_pages_count

        # Here data for Surahs needs to be deleted, so test that checks overall number of surahs doesn't fail
        db_session.query(SurahInMushaf).filter(SurahInMushaf.surah_number >= 500).delete()
        db_session.query(Surah).filter(Surah.id >= 500).delete()
        db_session.commit()
