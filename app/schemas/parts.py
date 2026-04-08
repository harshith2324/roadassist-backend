from pydantic import BaseModel
from typing import Optional


class SparePartCreate(BaseModel):
    part_name: str
    part_number: str | None = None
    quantity: int
    min_threshold: int = 2
    price: float
    compatible_vehicles: list[str] = []


class SparePartUpdate(BaseModel):
    part_name: str | None = None
    quantity: int | None = None
    min_threshold: int | None = None
    price: float | None = None


class SparePartOut(BaseModel):
    id: str
    mechanic_id: str
    part_name: str
    part_number: str | None
    quantity: int
    min_threshold: int
    price: float
    compatible_vehicles: list[str]
    is_low_stock: bool = False

    model_config = {"from_attributes": True}


class PartSearchResult(BaseModel):
    part_id: str
    part_name: str
    part_number: str | None
    quantity: int
    price: float
    mechanic_id: str
    mechanic_name: str
    mechanic_address: str | None
    mechanic_rating: float
    distance_km: float
