import uuid
from sqlalchemy import String, Integer, Numeric, ForeignKey, DateTime, text, ARRAY, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.session import Base


class SparePart(Base):
    __tablename__ = "spare_parts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    mechanic_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("mechanics.id", ondelete="CASCADE"), nullable=False)
    part_name: Mapped[str] = mapped_column(String(150), nullable=False)
    part_number: Mapped[str | None] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_threshold: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    compatible_vehicles: Mapped[list] = mapped_column(
        ARRAY(SAEnum("car", "bike", "truck", "suv", "other", name="vehicle_type")), default=[]
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    mechanic = relationship("Mechanic", back_populates="spare_parts")
    alerts = relationship("Alert", back_populates="part")
