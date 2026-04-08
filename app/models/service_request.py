import uuid
from sqlalchemy import String, Numeric, ForeignKey, DateTime, text, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geography
from datetime import datetime
from app.db.session import Base


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    mechanic_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("mechanics.id"), nullable=True)
    vehicle_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vehicles.id"), nullable=False)
    problem_desc: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum("requested", "accepted", "in_progress", "completed", "cancelled", name="request_status"),
        nullable=False, default="requested"
    )
    owner_location: Mapped[object] = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    total_cost: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    owner = relationship("User", back_populates="service_requests", foreign_keys=[owner_id])
    mechanic = relationship("Mechanic", back_populates="service_requests")
    vehicle = relationship("Vehicle", back_populates="service_requests")
    job_updates = relationship("JobUpdate", back_populates="request", order_by="JobUpdate.created_at")
    review = relationship("Review", back_populates="request", uselist=False)


class JobUpdate(Base):
    __tablename__ = "job_updates"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum("requested", "accepted", "in_progress", "completed", "cancelled", name="request_status"),
        nullable=False
    )
    updated_by: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    request = relationship("ServiceRequest", back_populates="job_updates")
