from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.db.session import get_db
from app.models.user import User
from app.models.mechanic import Mechanic
from app.core.security import require_role

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/analytics")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    summary = await db.execute(text("""
        SELECT
            COUNT(*)                                                        AS total_requests,
            COUNT(*) FILTER (WHERE status = 'completed')                   AS completed,
            COUNT(*) FILTER (WHERE status = 'cancelled')                   AS cancelled,
            COUNT(*) FILTER (WHERE status IN ('requested','accepted','in_progress')) AS active,
            COALESCE(SUM(total_cost) FILTER (WHERE status = 'completed'), 0) AS total_revenue,
            ROUND(AVG(total_cost) FILTER (WHERE status = 'completed'), 2)  AS avg_job_value
        FROM service_requests
    """))
    stats = dict(summary.mappings().first())

    top_parts = await db.execute(text("""
        SELECT sp.part_name, SUM(srp.quantity_used) AS times_used
        FROM service_request_parts srp
        JOIN spare_parts sp ON sp.id = srp.part_id
        GROUP BY sp.part_name
        ORDER BY times_used DESC
        LIMIT 10
    """))

    users_by_role = await db.execute(text("""
        SELECT role, COUNT(*) AS count FROM users GROUP BY role
    """))

    return {
        "summary": stats,
        "top_parts": [dict(r) for r in top_parts.mappings().all()],
        "users_by_role": {r["role"]: r["count"] for r in users_by_role.mappings().all()},
    }


@router.get("/mechanics")
async def list_all_mechanics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(text("""
        SELECT m.id, u.name, u.email, u.phone,
               m.specialization, m.is_available,
               CAST(m.rating AS FLOAT) AS rating,
               m.total_reviews, m.address
        FROM mechanics m
        JOIN users u ON u.id = m.user_id
        ORDER BY m.rating DESC
    """))
    return [dict(r) for r in result.mappings().all()]


@router.patch("/mechanics/{mechanic_id}/deactivate", status_code=200)
async def deactivate_mechanic(
    mechanic_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(Mechanic).where(Mechanic.id == mechanic_id))
    mechanic = result.scalar_one_or_none()
    if not mechanic:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Mechanic not found")

    await db.execute(
        text("UPDATE users SET is_active = FALSE WHERE id = :uid"),
        {"uid": mechanic.user_id},
    )
    await db.commit()
    return {"detail": "Mechanic deactivated"}
