from typing import Optional
from pydantic import BaseModel


class TrackResponse(BaseModel):
    id: str
    artist: str
    title: str
    difficulty: float
    level: int
    genre: str
    bpm: int
    released: str

    @classmethod
    def from_mongo(cls, doc: dict) -> "TrackResponse":
        # MongoDB stores _id as ObjectId; the API always exposes it as a string.
        return cls(id=str(doc["_id"]), **{k: v for k, v in doc.items() if k != "_id"})


class AverageDifficultyResponse(BaseModel):
    average_difficulty: Optional[float]


class PaginatedResponse(BaseModel):
    items: list[TrackResponse]
    per_page: int
    # None means there are no more pages; a value means pass it as ?after=
    # on the next request.
    next_cursor: Optional[str] = None
