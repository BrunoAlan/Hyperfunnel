from sqlalchemy import Column, Float, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    hotel = relationship("Hotel", back_populates="rooms")
