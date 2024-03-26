# tests/conftest.py
import os
import sys
import uuid
from typing import Any

import pytest

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

USER_1: Any = None
USER_2: Any = None


@pytest.fixture
def db_session():
    from src.dal.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def user1(db_session):
    global USER_1
    USER_1 = get_user(db_session, USER_1, 1)
    return USER_1


@pytest.fixture
def user2(db_session):
    global USER_2
    USER_2 = get_user(db_session, USER_2, 2)
    return USER_2


@pytest.fixture
def mushaf(db_session):
    from src.services import mushafs as mushafs_service
    from src.dal.enums import RiwayahEnum, PublisherEnum
    mushaf_object = mushafs_service.get_mushaf_if_exists(db_session, RiwayahEnum.QALOON, PublisherEnum.MADINA)
    if not mushaf_object:
        mushaf_object = mushafs_service.create_mushaf(db_session, RiwayahEnum.QALOON, PublisherEnum.MADINA)
    return mushaf_object


def get_user(db_session, user, user_index):
    from src.dal.models import User
    from src.services.users import create_user

    if user is not None:
        return user

    user_data = {
        'id': f'{uuid.uuid4()}_test',
        'alias': f'{uuid.uuid4()}_test_alias_{user_index}',
        'name': f'test_name_{user_index}',
        'surname': f'test_surname_{user_index}'}
    user = User(**user_data)

    create_user(db_session, user)
    return user


def pytest_unconfigure(config):  # noqa
    from sqlalchemy.orm import joinedload
    from src.dal.database import SessionLocal
    from src.dal.models import Ayah, AyahPart, AyahPartText, MushafPage, AyahPartMarker, Surah, SurahInMushaf
    from src.services.users import delete_user
    global USER_1, USER_2

    db = SessionLocal()
    try:
        if USER_1 is not None:
            delete_user(db, USER_1.id)
        if USER_2 is not None:
            delete_user(db, USER_2.id)

        markers_ids_to_delete = list()
        ayah_part_ids_to_delete = list()

        ayah_parts_to_delete = db.query(AyahPart).filter(
            AyahPart.ayah.has(Ayah.ayah_in_surah_number >= 1000)
        ).options(joinedload(AyahPart.markers)).all()

        for ayah_part in ayah_parts_to_delete:
            markers_ids = [marker.id for marker in ayah_part.markers]
            markers_ids_to_delete.extend(markers_ids)
            ayah_part_ids_to_delete.append(ayah_part.id)

        db.query(AyahPartMarker).filter(AyahPartMarker.id.in_(markers_ids_to_delete)).delete()
        db.query(AyahPart).filter(AyahPart.id.in_(ayah_part_ids_to_delete)).delete()

        db.query(AyahPartText).filter(AyahPartText.text.in_(
            ["Test text data upload", "Test text data upload. Part 0",
             "Test text data upload. Part 1", "Text that must not be created", "Test text data upload. Updated text"])
        ).delete()

        db.query(SurahInMushaf).filter(SurahInMushaf.surah_number >= 500).delete()
        db.query(Surah).filter(Surah.id >= 500).delete()
        db.query(MushafPage).filter(MushafPage.index >= 5000).delete()
        db.query(Ayah).filter(Ayah.ayah_in_surah_number >= 1000).delete()

        db.commit()

    finally:
        db.close()
