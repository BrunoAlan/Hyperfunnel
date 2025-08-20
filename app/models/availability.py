from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    ForeignKey,
    Date,
    Boolean,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class Availability(Base):
    __tablename__ = "availability"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    date = Column(Date, nullable=False)
    total_rooms = Column(
        Integer, nullable=False, default=5
    )  # Total habitaciones de este tipo
    available_rooms = Column(
        Integer, nullable=False, default=5
    )  # Habitaciones disponibles
    price_override = Column(
        Float, nullable=True
    )  # Precio especial para esta fecha (opcional)
    is_blocked = Column(Boolean, default=False)  # Para bloquear fechas específicas
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    room = relationship("Room", back_populates="availability")

    @property
    def is_available(self) -> bool:
        """Check if there are available rooms for this date"""
        return not self.is_blocked and self.available_rooms > 0

    @property
    def effective_price(self) -> float:
        """Get the effective price for this date (override or room's base price)"""
        return (
            self.price_override if self.price_override is not None else self.room.price
        )
