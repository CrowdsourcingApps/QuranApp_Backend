from src.dal.enums import RiwayahEnum, PublisherEnum
from src.mappers.recording_mapper import map_create_request_to_model
from src.models import AyahPartSearch, RecordingCreate


def test_map_create_request_to_model():
    recording_create = map_create_request_to_model(
        start_surah_number=1,
        start_ayah_in_surah_number=1,
        start_part_number=0,
        end_surah_number=2,
        end_ayah_in_surah_number=2,
        end_part_number=1,
        riwayah=RiwayahEnum.QALOON,
        publisher=PublisherEnum.MADINA)

    assert recording_create is not None
    assert type(recording_create) is RecordingCreate
    assert recording_create.riwayah == RiwayahEnum.QALOON
    assert recording_create.start == (AyahPartSearch(surah_number=1, ayah_in_surah_number=1, part_number=0))
    assert recording_create.end == (AyahPartSearch(surah_number=2, ayah_in_surah_number=2, part_number=1))
