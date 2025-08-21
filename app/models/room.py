from sqlalchemy import (
    Column,
    Float,
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import json
from ..database import Base
from typing import Optional, List


class Room(Base):
    __tablename__ = "rooms"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    hotel_id = Column(UUID(as_uuid=True), ForeignKey("hotels.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    guest = Column(Integer, nullable=False, default=4)
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
