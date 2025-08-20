from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from ..models.booking import BookingStatus


class BookingBase(BaseModel):
    hotel: UUID
    room: UUID
    price: float = Field(..., gt=0)
    status: BookingStatus = BookingStatus.PENDING


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    hotel: Optional[UUID] = None
    room: Optional[UUID] = None
    price: Optional[float] = Field(None, gt=0)
    status: Optional[BookingStatus] = None


class Booking(BookingBase):
    booking_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BookingWithDetails(Booking):
    """Booking response with hotel and room details"""

    hotel_name: Optional[str] = None
    hotel_city: Optional[str] = None
    hotel_country: Optional[str] = None
    room_name: Optional[str] = None
    room_description: Optional[str] = None
