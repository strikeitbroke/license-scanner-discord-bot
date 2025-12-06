from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime


class Result(BaseModel):
    plate: str | None = None


class PlateAPIResponse(BaseModel):
    processing_time: Decimal | None = None
    results: list[Result] | None = None


class MessageBase(BaseModel):
    channel_id: int
    plate_number: str | None = None
    sent_at: datetime
    author: str


class MessageCreate(MessageBase):
    pass
