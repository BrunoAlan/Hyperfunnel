from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import json
from .. import database
from ..models import Room, Hotel
from ..schemas import (
    Room as RoomSchema,
    RoomCreate,
    RoomUpdate,
    Hotel as HotelSchema,
)
from ..schemas.relationships import RoomWithHotel

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=List[RoomSchema])
def get_rooms(db: Session = Depends(database.get_db)):
    """Get all rooms"""
    rooms = db.query(Room).all()

    # Convert images and amenities JSON string to list for each room
    for room in rooms:
        if hasattr(room, "images_list"):
            room.images = room.images_list
        if hasattr(room, "amenities_list"):
            room.amenities = room.amenities_list

    return rooms


@router.get("/by-hotel/{hotel_id}", response_model=List[RoomSchema])
def get_rooms_by_hotel(hotel_id: str, db: Session = Depends(database.get_db)):
    """Get all rooms for a specific hotel"""
    try:
        # Validate that hotel_id is a valid UUID
        hotel_uuid = UUID(hotel_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid hotel ID format. Must be a valid UUID."
        )

    # Check if hotel exists
    hotel = db.query(Hotel).filter(Hotel.id == hotel_uuid).first()
    if hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")

    # Get all rooms for this hotel
    rooms = db.query(Room).filter(Room.hotel_id == hotel_uuid).all()

    # Convert images and amenities JSON string to list for each room
    for room in rooms:
        if hasattr(room, "images_list"):
            room.images = room.images_list
        if hasattr(room, "amenities_list"):
            room.amenities = room.amenities_list

    return rooms


@router.get("/{room_id}", response_model=RoomSchema)
def get_room(room_id: str, db: Session = Depends(database.get_db)):
    """Get a specific room by ID"""
    try:
        # Validate that room_id is a valid UUID
        room_uuid = UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid room ID format. Must be a valid UUID."
        )

    room = db.query(Room).filter(Room.id == room_uuid).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    # Convert images and amenities JSON string to list for API response
    if hasattr(room, "images_list"):
        room.images = room.images_list
    if hasattr(room, "amenities_list"):
        room.amenities = room.amenities_list

    return room


@router.get("/{room_id}/with-hotel", response_model=RoomWithHotel)
def get_room_with_hotel(room_id: str, db: Session = Depends(database.get_db)):
    """Get a room with its hotel information"""
    try:
        # Validate that room_id is a valid UUID
        room_uuid = UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid room ID format. Must be a valid UUID."
        )

    room = db.query(Room).filter(Room.id == room_uuid).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    # Convert images and amenities JSON string to list for API response
    if hasattr(room, "images_list"):
        room.images = room.images_list
    if hasattr(room, "amenities_list"):
        room.amenities = room.amenities_list

    # Get hotel information
    hotel = db.query(Hotel).filter(Hotel.id == room.hotel_id).first()
    if hotel:
        # Convert hotel images JSON string to list for API response
        if hasattr(hotel, "images_list"):
            hotel.images = hotel.images_list
        # Add hotel to room object
        room.hotel = hotel

    return room


@router.post("", response_model=RoomSchema)
def create_room(room_data: dict, db: Session = Depends(database.get_db)):
    """Create a new room"""
    try:
        # Validate that hotel_id is a valid UUID
        hotel_uuid = UUID(room_data["hotel_id"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=400, detail="Invalid or missing hotel_id. Must be a valid UUID."
        )

    # Check if hotel exists
    hotel = db.query(Hotel).filter(Hotel.id == hotel_uuid).first()
    if hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")

    # Convert images list to JSON string for storage
    images_json = None
    if room_data.get("images"):
        images_json = json.dumps(room_data["images"])

    # Convert amenities list to JSON string for storage
    amenities_json = None
    if room_data.get("amenities"):
        amenities_json = json.dumps(room_data["amenities"])

    db_room = Room(
        hotel_id=hotel_uuid,
        name=room_data["name"],
        description=room_data.get("description"),
        price=room_data["price"],
        images=images_json,
        amenities=amenities_json,
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)

    # Convert images and amenities back to list for API response
    if hasattr(db_room, "images_list"):
        db_room.images = db_room.images_list
    if hasattr(db_room, "amenities_list"):
        db_room.amenities = db_room.amenities_list

    return db_room


@router.put("/{room_id}", response_model=RoomSchema)
def update_room(
    room_id: str,
    room_update: RoomUpdate,
    db: Session = Depends(database.get_db),
):
    """Update a room completely"""
    try:
        # Validate that room_id is a valid UUID
        room_uuid = UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid room ID format. Must be a valid UUID."
        )

    # Check if room exists
    db_room = db.query(Room).filter(Room.id == room_uuid).first()
    if db_room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    # Update only the fields that are provided
    update_data = room_update.model_dump(exclude_unset=True)

    # Handle images conversion if provided
    if "images" in update_data:
        update_data["images"] = json.dumps(update_data["images"])

    # Handle amenities conversion if provided
    if "amenities" in update_data:
        update_data["amenities"] = json.dumps(update_data["amenities"])

    # Update the room
    for field, value in update_data.items():
        setattr(db_room, field, value)

    db.commit()
    db.refresh(db_room)

    # Convert images and amenities back to list for API response
    if hasattr(db_room, "images_list"):
        db_room.images = db_room.images_list
    if hasattr(db_room, "amenities_list"):
        db_room.amenities = db_room.amenities_list

    return db_room
