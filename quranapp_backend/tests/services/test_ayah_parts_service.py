from src.dal.enums import RiwayahEnum, PublisherEnum
from src.models import AyahPartSearch
from src.services import ayah_parts


def test_get_ayah_part(db_session):
    ayah_part = ayah_parts.get_ayah_part(
        db_session, AyahPartSearch(surah_number=1, ayah_in_surah_number=0, part_number=0), RiwayahEnum.QALOON, PublisherEnum.MADINA)  # noqa

    assert ayah_part is not None
