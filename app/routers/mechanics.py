from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.models.mechanic import Mechanic
from app.core.security import get_current_user, require_role
from app.schemas.mechanic import (
    MechanicNearbyResult, MechanicUpdate, MechanicProfile, MechanicDashboard
)

router = APIRouter(prefix="/mechanics", tags=["Mechanics"])


# ------------------------------------------------------------------
# GET /mechanics/nearby  — geospatial search (core feature)
# Uses PostGIS ST_DWithin + ST_Distance, hits the GIST index
# ------------------------------------------------------------------
@router.get("/nearby", response_model=list[MechanicNearbyResult])
async def get_nearby_mechanics(
    lat: float = Query(..., description="Your latitude"),
    lng: float = Query(..., description="Your longitude"),
    radius_km: float = Query(10.0, ge=1, le=50, description="Search radius in km"),
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type"),
    db: AsyncSession = Depends(get_db),
):
    vehicle_filter = ""
    params: dict = {"lat": lat, "lng": lng, "radius_m": radius_km * 1000}

    if vehicle_type:
        vehicle_filter = "AND :vtype = ANY(m.vehicle_types)"
        params["vtype"] = vehicle_type

    query = text(f"""
        SELECT
            m.id                                                        AS mechanic_id,
            m.user_id,
            u.name,
            u.phone,
            m.address,
            m.specialization,
            m.vehicle_types,
            m.is_available,
            CAST(m.rating AS FLOAT)                                     AS rating,
            m.total_reviews,
            ROUND(
                CAST(ST_Distance(
                    m.location,
                    ST_MakePoint(:lng, :lat)::GEOGRAPHY
                ) / 1000 AS NUMERIC), 2
            )                                                           AS distance_km
        FROM mechanics m
        JOIN users u ON u.id = m.user_id
        WHERE
            u.is_active = TRUE
            AND m.is_available = TRUE
            AND ST_DWithin(
                m.location,
                ST_MakePoint(:lng, :lat)::GEOGRAPHY,
                :radius_m
            )
            {vehicle_filter}
        ORDER BY distance_km ASC, m.rating DESC
    """)

    result = await db.execute(query, params)
    rows = result.mappings().all()
    return [MechanicNearbyResult(**dict(r)) for r in rows]


# ------------------------------------------------------------------
# GET /mechanics/:id  — public mechanic profile
# ------------------------------------------------------------------
@router.get("/{mechanic_id}", response_model=MechanicProfile)
async def get_mechanic(mechanic_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Mechanic).where(Mechanic.id == mechanic_id)
    )
    mechanic = result.scalar_one_or_none()
    if not mechanic:
        raise HTTPException(status_code=404, detail="Mechanic not found")
    return mechanic


# ------------------------------------------------------------------
# GET /mechanics/:id/dashboard  — mechanic's own dashboard
# Reads from the materialized view mv_mechanic_dashboard
# ------------------------------------------------------------------
@router.get("/{mechanic_id}/dashboard", response_model=MechanicDashboard)
async def get_mechanic_dashboard(
    mechanic_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Mechanics can only see their own dashboard; admins can see all
    if current_user.role == "mechanic":
        result = await db.execute(
            select(Mechanic).where(Mechanic.user_id == current_user.id)
        )
        mechanic = result.scalar_one_or_none()
        if not mechanic or mechanic.id != mechanic_id:
            raise HTTPException(status_code=403, detail="Access denied")

    row = await db.execute(
        text("SELECT * FROM mv_mechanic_dashboard WHERE mechanic_id = :mid"),
        {"mid": mechanic_id},
    )
    data = row.mappings().first()
    if not data:
        raise HTTPException(status_code=404, detail="Dashboard data not found")
    return MechanicDashboard(**dict(data))


# ------------------------------------------------------------------
# PATCH /mechanics/me  — mechanic updates their own profile
# ------------------------------------------------------------------
@router.patch("/me", response_model=MechanicProfile)
async def update_my_profile(
    payload: MechanicUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("mechanic")),
):
    result = await db.execute(
        select(Mechanic).where(Mechanic.user_id == current_user.id)
    )
    mechanic = result.scalar_one_or_none()
    if not mechanic:
        raise HTTPException(status_code=404, detail="Mechanic profile not found")

    if payload.address is not None:
        mechanic.address = payload.address
    if payload.specialization is not None:
        mechanic.specialization = payload.specialization
    if payload.vehicle_types is not None:
        mechanic.vehicle_types = payload.vehicle_types
    if payload.is_available is not None:
        mechanic.is_available = payload.is_available

    # Update location if lat/lng provided
    if payload.lat is not None and payload.lng is not None:
        await db.execute(
            text("UPDATE mechanics SET location = ST_MakePoint(:lng, :lat)::GEOGRAPHY WHERE id = :mid"),
            {"lng": payload.lng, "lat": payload.lat, "mid": mechanic.id},
        )

    await db.commit()
    await db.refresh(mechanic)
    return mechanic
