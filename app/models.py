from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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


class RatingInput(BaseModel):
    track_id: str
    rating: float = Field(ge=1, le=5)


class RatingResponse(BaseModel):
    id: str
    track_id: str
    rating: float
    created_at: datetime

    @classmethod
    def from_mongo(cls, doc: dict) -> "RatingResponse":
        return cls(
            id=str(doc["_id"]),
            track_id=str(doc["track_id"]),
            rating=doc["rating"],
            created_at=doc["created_at"],
        )


class RatingStatsResponse(BaseModel):
    average: Optional[float]
    min: Optional[float]
    max: Optional[float]


class PaginatedResponse(BaseModel):
    items: list[TrackResponse]
    per_page: int
    # None means there are no more pages; a value means pass it as ?after=
    # on the next request.
    next_cursor: Optional[str] = None
