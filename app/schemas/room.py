import json
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class RoomBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    guest: int = Field(
        ..., gt=0, description="Number of guests the room can accommodate"
    )
    images: Optional[List[str]] = Field(None, description="List of image URLs")
    amenities: Optional[List[str]] = Field(None, description="List of room amenities")


class RoomCreate(RoomBase):
    pass


class RoomCreateWithHotel(RoomBase):
    hotel_id: UUID


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(
        None, gt=0, description="Price must be greater than 0"
    )
    guest: Optional[int] = Field(None, gt=0, description="Number of guests")
    images: Optional[List[str]] = Field(None, description="List of image URLs")
    amenities: Optional[List[str]] = Field(None, description="List of room amenities")


class RoomUpdateDB(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(
        None, gt=0, description="Price must be greater than 0"
    )
    guest: Optional[int] = Field(None, gt=0, description="Number of guests")
    images: Optional[str] = Field(None, description="JSON string of image URLs")
    amenities: Optional[str] = Field(None, description="JSON string of amenities")


class Room(RoomBase):
    id: UUID
    hotel_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @field_validator("images", mode="before")
    @classmethod
    def validate_images(cls, v, info):
        # If the source object has images_list property, use it
        if hasattr(info.context, "images_list") if info.context else False:
            return info.context.images_list
        # If it's a SQLAlchemy object with images_list property
        elif hasattr(v, "images_list"):
            return v.images_list
        # If it's a JSON string, parse it
        elif isinstance(v, str) and v:
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v

    @field_validator("amenities", mode="before")
    @classmethod
    def validate_amenities(cls, v, info):
        # If the source object has amenities_list property, use it
        if hasattr(info.context, "amenities_list") if info.context else False:
            return info.context.amenities_list
        # If it's a SQLAlchemy object with amenities_list property
        elif hasattr(v, "amenities_list"):
            return v.amenities_list
        # If it's a JSON string, parse it
        elif isinstance(v, str) and v:
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v
