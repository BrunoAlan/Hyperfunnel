from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import json
from ..database import Base
from typing import Optional, List


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

    @property
    def images_list(self) -> Optional[List[str]]:
        """Convert images JSON string to list"""
        if self.images:
            try:
                return json.loads(self.images)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @images_list.setter
    def images_list(self, value: Optional[List[str]]):
        """Convert images list to JSON string"""
        if value is not None:
            self.images = json.dumps(value)
        else:
            self.images = None
