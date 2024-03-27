from sqlalchemy.orm import Session

from src.dal.enums import RiwayahEnum
from src.dal.models import Reciter


def get_reciter(db: Session, name: str, riwayah: RiwayahEnum) -> Reciter | None:
    reciter = db.query(Reciter).filter_by(name=name, riwayah=riwayah).first()
    if reciter is not None:
        db.expunge(reciter)
    return reciter
