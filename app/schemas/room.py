import json
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class RoomBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0, description="Price must be greater than 0")
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
    images: Optional[List[str]] = Field(None, description="List of image URLs")
    amenities: Optional[List[str]] = Field(None, description="List of room amenities")


class RoomUpdateDB(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(
        None, gt=0, description="Price must be greater than 0"
    )
    images: Optional[str] = Field(None, description="JSON string of image URLs")
    amenities: Optional[str] = Field(None, description="JSON string of amenities")


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
        # Convert amenities JSON string to list for API response
        if hasattr(obj, "amenities_list"):
            obj.amenities = obj.amenities_list
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
