from sqlalchemy.orm import Session

from src.dal.enums import RiwayahEnum, PublisherEnum
from src.dal.models import Mushaf


def create_mushaf(db: Session, riwayah: RiwayahEnum, publisher: PublisherEnum) -> Mushaf:
    db_mushaf = Mushaf(riwayah=riwayah, publisher=publisher)
    db.add(db_mushaf)
    db.commit()
    db.refresh(db_mushaf)
    return db_mushaf


def get_mushaf_if_exists(db: Session, riwayah: RiwayahEnum, publisher: PublisherEnum) -> Mushaf | None:
    return db.query(Mushaf).filter_by(riwayah=riwayah, publisher=publisher).first()


def get_or_create_mushaf(db: Session, riwayah: RiwayahEnum, publisher: PublisherEnum) -> Mushaf:
    mushaf = get_mushaf_if_exists(db, riwayah, publisher)
    if not mushaf:
        mushaf = create_mushaf(db, riwayah, publisher)
    return mushaf
