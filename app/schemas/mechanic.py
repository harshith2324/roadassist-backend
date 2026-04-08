from pydantic import BaseModel
from typing import Optional


class MechanicNearbyResult(BaseModel):
    mechanic_id: str
    user_id: str
    name: str
    phone: str | None
    address: str | None
    specialization: str | None
    vehicle_types: list[str]
    is_available: bool
    rating: float
    total_reviews: int
    distance_km: float

    model_config = {"from_attributes": True}


class MechanicUpdate(BaseModel):
    address: str | None = None
    specialization: str | None = None
    vehicle_types: list[str] | None = None
    is_available: bool | None = None
    lat: float | None = None
    lng: float | None = None


class MechanicProfile(BaseModel):
    id: str
    user_id: str
    address: str | None
    specialization: str | None
    vehicle_types: list[str]
    is_available: bool
    rating: float
    total_reviews: int

    model_config = {"from_attributes": True}


class MechanicDashboard(BaseModel):
    mechanic_id: str
    mechanic_name: str
    rating: float
    total_reviews: int
    total_jobs: int
    completed_jobs: int
    active_jobs: int
    total_earnings: float
    earnings_this_week: float
