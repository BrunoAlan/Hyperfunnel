from sqlalchemy import (
    Column,
    String,
    DateTime,
    Date,
    ForeignKey,
    Float,
    Enum,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import enum


class BookingStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )

    # Foreign keys
    hotel = Column(UUID(as_uuid=True), ForeignKey("hotels.id"), nullable=False)
    room = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)

    # Booking dates
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)

    # Guest information
    guests = Column(Integer, nullable=False, default=1)

    # Pricing
    price = Column(Float, nullable=False)

    # Status
    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    hotel_ref = relationship("Hotel", foreign_keys=[hotel], backref="bookings")
    room_ref = relationship("Room", foreign_keys=[room], backref="bookings")

    @property
    def nights(self) -> int:
        """Calculate the number of nights for this booking"""
        return (self.check_out_date - self.check_in_date).days

    @property
    def total_price(self) -> float:
        """Calculate total price based on nights and guests"""
        return self.price * self.nights

    def __repr__(self):
        return f"<Booking {self.booking_id}: {self.status} ({self.check_in_date} to {self.check_out_date})>"
