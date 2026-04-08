import uuid
from sqlalchemy import String, Boolean, Enum as SAEnum, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    role: Mapped[str] = mapped_column(
        SAEnum("owner", "mechanic", "admin", name="user_role"), nullable=False, default="owner"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )

    # Relationships
    mechanic_profile = relationship("Mechanic", back_populates="user", uselist=False)
    vehicles = relationship("Vehicle", back_populates="owner")
    service_requests = relationship("ServiceRequest", back_populates="owner", foreign_keys="ServiceRequest.owner_id")
    reviews = relationship("Review", back_populates="owner")
