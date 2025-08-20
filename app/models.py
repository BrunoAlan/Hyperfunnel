from sqlalchemy import (
    Column,
    Float,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Date,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import json
from .database import Base
from typing import Optional, List


class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    name = Column(String(200), nullable=False)
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    stars = Column(Integer)
    images = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    rooms = relationship("Room", back_populates="hotel", cascade="all, delete-orphan")

    @property
    def images_list(self) -> Optional[List[str]]:
        """Convert images JSON string to list"""
        if self.images:
            try:
                return json.loads(self.images)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @images_list.setter
    def images_list(self, value: Optional[List[str]]):
        """Convert images list to JSON string"""
        if value is not None:
            self.images = json.dumps(value)
        else:
            self.images = None


class Room(Base):
    __tablename__ = "rooms"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    hotel_id = Column(UUID(as_uuid=True), ForeignKey("hotels.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    images = Column(Text, nullable=True)
    amenities = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    hotel = relationship("Hotel", back_populates="rooms")
    availability = relationship(
        "Availability", back_populates="room", cascade="all, delete-orphan"
    )

    @property
    def images_list(self) -> Optional[List[str]]:
        """Convert images JSON string to list"""
        if self.images:
            try:
                return json.loads(self.images)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @images_list.setter
    def images_list(self, value: Optional[List[str]]):
        """Convert images list to JSON string"""
        if value is not None:
            self.images = json.dumps(value)
        else:
            self.images = None

    @property
    def amenities_list(self) -> Optional[List[str]]:
        """Convert amenities JSON string to list"""
        if self.amenities:
            try:
                return json.loads(self.amenities)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @amenities_list.setter
    def amenities_list(self, value: Optional[List[str]]):
        """Convert amenities list to JSON string"""
        if value is not None:
            self.amenities = json.dumps(value)
        else:
            self.amenities = None


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
