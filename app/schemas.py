from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class HotelBase(BaseModel):
    name: str
    country: str
    city: str
    stars: int = Field(None, ge=1, le=5, description="Number of stars (1-5)")
    images: Optional[str] = None


class HotelCreate(HotelBase):
    pass


class HotelUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    stars: Optional[int] = Field(None, ge=1, le=5, description="Number of stars (1-5)")
    images: Optional[str] = None


class RoomBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    images: Optional[str] = None


class RoomCreate(RoomBase):
    pass


class Room(RoomBase):
    id: UUID
    hotel_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Hotel(HotelBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HotelWithRooms(Hotel):
    rooms: List[Room] = []


class RoomWithHotel(Room):
    hotel: Hotel
