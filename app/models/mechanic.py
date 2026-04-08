import uuid
from sqlalchemy import String, Boolean, Numeric, Integer, ForeignKey, DateTime, text, ARRAY, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geography
from datetime import datetime
from app.db.session import Base


class Mechanic(Base):
    __tablename__ = "mechanics"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    location: Mapped[object] = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    address: Mapped[str | None] = mapped_column()
    specialization: Mapped[str | None] = mapped_column()
    vehicle_types: Mapped[list] = mapped_column(
        ARRAY(SAEnum("car", "bike", "truck", "suv", "other", name="vehicle_type")), default=[]
    )
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(3, 2), default=0.00, nullable=False)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    # Relationships
    user = relationship("User", back_populates="mechanic_profile")
    spare_parts = relationship("SparePart", back_populates="mechanic")
    service_requests = relationship("ServiceRequest", back_populates="mechanic")
    alerts = relationship("Alert", back_populates="mechanic")
    reviews = relationship("Review", back_populates="mechanic")
