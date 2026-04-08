import uuid
from sqlalchemy import SmallInteger, Text, ForeignKey, DateTime, text, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.session import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("service_requests.id"), unique=True, nullable=False)
    owner_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    mechanic_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("mechanics.id"), nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    request = relationship("ServiceRequest", back_populates="review")
    owner = relationship("User", back_populates="reviews")
    mechanic = relationship("Mechanic", back_populates="reviews")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    mechanic_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("mechanics.id", ondelete="CASCADE"), nullable=False)
    part_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("spare_parts.id", ondelete="SET NULL"), nullable=True)
    alert_type: Mapped[str] = mapped_column(
        SAEnum("low_stock", "new_request", "system", name="alert_type"), nullable=False, default="low_stock"
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    mechanic = relationship("Mechanic", back_populates="alerts")
    part = relationship("SparePart", back_populates="alerts")
