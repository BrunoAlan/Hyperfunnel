"""
Schemas with relationships to avoid circular imports
"""

from typing import List
from .hotel import Hotel
from .room import Room


class HotelWithRooms(Hotel):
    rooms: List[Room] = []


class RoomWithHotel(Room):
    hotel: Hotel
