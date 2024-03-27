import uuid

from pydantic import BaseModel, ConfigDict


class AyahPartMarker(BaseModel):
    id: uuid.UUID
    order: int
    x: int
    y1: int
    y2: int
    is_new_line: bool

    model_config = ConfigDict(from_attributes=True)
