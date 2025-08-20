import json
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date


class HotelBase(BaseModel):
    name: str
    country: str
    city: str
    stars: int = Field(None, ge=1, le=5, description="Number of stars (1-5)")
    images: Optional[List[str]] = Field(None, description="List of image URLs")


class HotelCreate(HotelBase):
    pass


class HotelUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    stars: Optional[int] = Field(None, ge=1, le=5, description="Number of stars (1-5)")
    images: Optional[List[str]] = Field(None, description="List of image URLs")


class HotelUpdateDB(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    stars: Optional[int] = Field(None, ge=1, le=5, description="Number of stars (1-5)")
    images: Optional[str] = Field(None, description="JSON string of image URLs")


class RoomBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    images: Optional[List[str]] = Field(None, description="List of image URLs")
    amenities: Optional[List[str]] = Field(None, description="List of room amenities")


class RoomCreate(RoomBase):
    pass


class Room(RoomBase):
    id: UUID
    hotel_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj):
        # Convert images JSON string to list for API response
        if hasattr(obj, "images_list"):
            obj.images = obj.images_list
        return super().model_validate(obj)

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


class Hotel(HotelBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj):
        # Convert images JSON string to list for API response
        if hasattr(obj, "images_list"):
            obj.images = obj.images_list
        return super().model_validate(obj)


class HotelWithRooms(Hotel):
    rooms: List[Room] = []


class RoomWithHotel(Room):
    hotel: Hotel


# Availability Schemas
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
    start_date: date
    end_date: date
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
    start_date: date
    end_date: date
    min_rooms: int = Field(
        default=1, ge=1, description="Minimum number of rooms needed"
    )
