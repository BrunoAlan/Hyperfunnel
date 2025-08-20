from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


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
