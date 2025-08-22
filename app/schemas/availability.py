from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from .room import Room


class AvailabilityBase(BaseModel):
    date: date
    total_rooms: int = Field(
        default=5, ge=1, le=10, description="Total rooms of this type (1-10)"
    )
    available_rooms: int = Field(
        default=5, ge=0, description="Available rooms for this date"
    )
    price_override: Optional[float] = Field(
        None, gt=0, description="Override price for this specific date"
    )
    is_blocked: bool = Field(default=False, description="Block this date from bookings")


class AvailabilityCreate(AvailabilityBase):
    room_id: UUID


class AvailabilityUpdate(BaseModel):
    available_rooms: Optional[int] = Field(
        None, ge=0, description="Available rooms for this date"
    )
    price_override: Optional[float] = Field(
        None, gt=0, description="Override price for this specific date"
    )
    is_blocked: Optional[bool] = Field(
        None, description="Block this date from bookings"
    )


class Availability(AvailabilityBase):
    id: UUID
    room_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AvailabilityWithRoom(Availability):
    room: Room


class AvailabilityRange(BaseModel):
    """Schema for creating availability for a range of dates"""

    room_id: UUID
    check_in_date: date
    check_out_date: date
    total_rooms: int = Field(
        default=5, ge=1, le=10, description="Total rooms of this type (1-10)"
    )
    available_rooms: int = Field(
        default=5, ge=0, description="Available rooms for this date"
    )
    price_override: Optional[float] = Field(
        None, gt=0, description="Override price for this date range"
    )
    is_blocked: bool = Field(
        default=False, description="Block these dates from bookings"
    )


class AvailabilitySearch(BaseModel):
    """Schema for searching availability"""

    hotel_id: Optional[UUID] = None
    room_id: Optional[UUID] = None
    check_in_date: date
    check_out_date: date
    min_rooms: int = Field(
        default=1, ge=1, description="Minimum number of rooms needed"
    )
    guests: int = Field(
        ge=1, description="Number of guests that need to be accommodated"
    )
