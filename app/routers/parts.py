from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.models.mechanic import Mechanic
from app.models.spare_part import SparePart
from app.core.security import get_current_user, require_role
from app.schemas.parts import SparePartCreate, SparePartUpdate, SparePartOut, PartSearchResult

router = APIRouter(prefix="/parts", tags=["Spare Parts"])


# ------------------------------------------------------------------
# GET /parts/search  — find a part across all nearby mechanics
# Cross-table geospatial + full-text search (shows off both indexes)
# ------------------------------------------------------------------
@router.get("/search", response_model=list[PartSearchResult])
async def search_parts(
    name: str = Query(..., min_length=2, description="Part name to search"),
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(15.0, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    query = text("""
        SELECT
            sp.id                                                       AS part_id,
            sp.part_name,
            sp.part_number,
            sp.quantity,
            CAST(sp.price AS FLOAT)                                     AS price,
            m.id                                                        AS mechanic_id,
            u.name                                                      AS mechanic_name,
            m.address                                                   AS mechanic_address,
            CAST(m.rating AS FLOAT)                                     AS mechanic_rating,
            ROUND(
                CAST(ST_Distance(
                    m.location,
                    ST_MakePoint(:lng, :lat)::GEOGRAPHY
                ) / 1000 AS NUMERIC), 2
            )                                                           AS distance_km
        FROM spare_parts sp
        JOIN mechanics m  ON m.id  = sp.mechanic_id
        JOIN users u      ON u.id  = m.user_id
        WHERE
            sp.quantity > 0
            AND m.is_available = TRUE
            AND u.is_active = TRUE
            AND to_tsvector('english', sp.part_name) @@ plainto_tsquery('english', :name)
            AND ST_DWithin(
                m.location,
                ST_MakePoint(:lng, :lat)::GEOGRAPHY,
                :radius_m
            )
        ORDER BY distance_km ASC, sp.price ASC
    """)

    result = await db.execute(query, {"name": name, "lat": lat, "lng": lng, "radius_m": radius_km * 1000})
    rows = result.mappings().all()
    return [PartSearchResult(**dict(r)) for r in rows]


# ------------------------------------------------------------------
# GET /mechanics/:id/parts  — all parts for a specific mechanic
# ------------------------------------------------------------------
@router.get("/mechanic/{mechanic_id}", response_model=list[SparePartOut])
async def get_mechanic_parts(mechanic_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SparePart).where(SparePart.mechanic_id == mechanic_id)
    )
    parts = result.scalars().all()
    return [
        SparePartOut(
            **{c.key: getattr(p, c.key) for c in p.__table__.columns},
            is_low_stock=p.quantity < p.min_threshold,
        )
        for p in parts
    ]


# ------------------------------------------------------------------
# POST /parts  — mechanic adds a new part to inventory
# ------------------------------------------------------------------
@router.post("", response_model=SparePartOut, status_code=201)
async def add_part(
    payload: SparePartCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("mechanic")),
):
    mech_result = await db.execute(
        select(Mechanic).where(Mechanic.user_id == current_user.id)
    )
    mechanic = mech_result.scalar_one_or_none()
    if not mechanic:
        raise HTTPException(status_code=404, detail="Mechanic profile not found")

    part = SparePart(
        mechanic_id=mechanic.id,
        **payload.model_dump(),
    )
    db.add(part)
    await db.commit()
    await db.refresh(part)

    return SparePartOut(
        **{c.key: getattr(part, c.key) for c in part.__table__.columns},
        is_low_stock=part.quantity < part.min_threshold,
    )


# ------------------------------------------------------------------
# PATCH /parts/:id  — mechanic updates a part (quantity, price, etc.)
# Triggers the DB low-stock alert trigger on quantity update
# ------------------------------------------------------------------
@router.patch("/{part_id}", response_model=SparePartOut)
async def update_part(
    part_id: str,
    payload: SparePartUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("mechanic")),
):
    mech_result = await db.execute(
        select(Mechanic).where(Mechanic.user_id == current_user.id)
    )
    mechanic = mech_result.scalar_one_or_none()

    result = await db.execute(
        select(SparePart).where(SparePart.id == part_id, SparePart.mechanic_id == mechanic.id)
    )
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found in your inventory")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(part, field, value)

    await db.commit()
    await db.refresh(part)

    return SparePartOut(
        **{c.key: getattr(part, c.key) for c in part.__table__.columns},
        is_low_stock=part.quantity < part.min_threshold,
    )


# ------------------------------------------------------------------
# DELETE /parts/:id  — mechanic removes a part
# ------------------------------------------------------------------
@router.delete("/{part_id}", status_code=204)
async def delete_part(
    part_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("mechanic")),
):
    mech_result = await db.execute(
        select(Mechanic).where(Mechanic.user_id == current_user.id)
    )
    mechanic = mech_result.scalar_one_or_none()

    result = await db.execute(
        select(SparePart).where(SparePart.id == part_id, SparePart.mechanic_id == mechanic.id)
    )
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")

    await db.delete(part)
    await db.commit()
