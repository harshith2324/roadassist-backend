from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


class ServiceRequestCreate(BaseModel):
    vehicle_id: str
    problem_desc: str
    lat: float
    lng: float


class StatusUpdate(BaseModel):
    status: Literal["accepted", "in_progress", "completed", "cancelled"]
    note: str | None = None


class JobUpdateOut(BaseModel):
    id: str
    status: str
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ServiceRequestOut(BaseModel):
    id: str
    owner_id: str
    mechanic_id: str | None
    vehicle_id: str
    problem_desc: str
    status: str
    total_cost: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ServiceRequestDetail(ServiceRequestOut):
    job_updates: list[JobUpdateOut] = []


class ReviewCreate(BaseModel):
    request_id: str
    rating: int
    comment: str | None = None

    def validate_rating(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewOut(BaseModel):
    id: str
    request_id: str
    mechanic_id: str
    rating: int
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
