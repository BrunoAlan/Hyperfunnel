from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from ..models.booking import BookingStatus


class BookingBase(BaseModel):
    hotel: UUID
    room: UUID
    check_in_date: date = Field(..., description="Check-in date")
    check_out_date: date = Field(..., description="Check-out date")
    guests: int = Field(default=1, ge=1, le=10, description="Number of guests")
    price: float = Field(..., gt=0, description="Price per night")
    status: BookingStatus = BookingStatus.PENDING

    @field_validator("check_out_date")
    @classmethod
    def validate_checkout_after_checkin(cls, v, info):
        if "check_in_date" in info.data and v <= info.data["check_in_date"]:
            raise ValueError("Check-out date must be after check-in date")
        return v

    @field_validator("check_in_date")
    @classmethod
    def validate_checkin_not_past(cls, v):
        if v < date.today():
            raise ValueError("Check-in date cannot be in the past")
        return v


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    hotel: Optional[UUID] = None
    room: Optional[UUID] = None
    check_in_date: Optional[date] = Field(None, description="Check-in date")
    check_out_date: Optional[date] = Field(None, description="Check-out date")
    guests: Optional[int] = Field(None, ge=1, le=10, description="Number of guests")
    price: Optional[float] = Field(None, gt=0, description="Price per night")
    status: Optional[BookingStatus] = None


class Booking(BookingBase):
    booking_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @property
    def nights(self) -> int:
        """Calculate the number of nights for this booking"""
        return (self.check_out_date - self.check_in_date).days

    @property
    def total_price(self) -> float:
        """Calculate total price based on nights"""
        return self.price * self.nights


class BookingWithDetails(Booking):
    """Booking response with hotel and room details"""

    hotel_name: Optional[str] = None
    hotel_city: Optional[str] = None
    hotel_country: Optional[str] = None
    room_name: Optional[str] = None
    room_description: Optional[str] = None
