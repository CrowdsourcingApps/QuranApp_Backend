import uuid

from src.dal.models import AyahPart as AyahPartDal, AyahPartText, Mushaf, ReciterAudio
from src.dal.models import AyahPartMarker as AyahPartMarkerDal
from src.models import MushafPageDetails, MushafPageAyahPart, AyahPartMarker


def map_to_page_details(page_id: uuid.UUID, ayah_parts: list[AyahPartDal]) -> MushafPageDetails:
    mapped_ayah_parts = []
    for ayah_part in ayah_parts:
        mapped_ayah_parts.append(MushafPageAyahPart(
            id=ayah_part.id,
            surah_title=ayah_part.ayah.surah.title_eng,
            part_number=ayah_part.part_number,
            surah_number=ayah_part.ayah.surah_number,
            ayah_in_surah_number=ayah_part.ayah.ayah_in_surah_number,
            text=_map_text(ayah_part.text),
            text_id=ayah_part.ayah_part_text_id,
            audio_link=_map_reciter_audio(ayah_part.reciter_audios, ayah_part.ayah.mushaf),
            markers=_map_ayah_part_markers(ayah_part.markers)
        ))

    return MushafPageDetails(
        page_id=page_id,
        ayah_parts_count=len(mapped_ayah_parts),
        ayah_parts=mapped_ayah_parts
    )


def _map_ayah_part_markers(markers: list[AyahPartMarkerDal]):
    mapped_markers = []
    for marker in markers:
        mapped_markers.append(AyahPartMarker(
            id=marker.id,
            order=marker.order,
            x=marker.x,
            y1=marker.y1,
            y2=marker.y2,
            is_new_line=marker.is_new_line
        ))

    return sorted(mapped_markers, key=lambda m: m.order)


def _map_text(text: AyahPartText) -> str | None:
    if text is None:
        return None

    return text.text


def _map_reciter_audio(reciter_audios: list[ReciterAudio], mushaf: Mushaf) -> str | None: # noqa
    if reciter_audios is None:
        return None

    audios = list(filter(lambda x: x.reciter.riwayah == mushaf.riwayah, reciter_audios))

    if len(audios) < 1:
        return None

    audio = audios[0]
    return audio.audio_link
