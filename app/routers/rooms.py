from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from .. import models, database, schemas

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("/", response_model=List[schemas.Room])
def get_rooms(db: Session = Depends(database.get_db)):
    rooms = db.query(models.Room).all()
    return rooms


@router.get("/{room_id}", response_model=schemas.Room)
def get_room(room_id: str, db: Session = Depends(database.get_db)):
    try:
        # Validate that room_id is a valid UUID
        room_uuid = UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid room ID format. Must be a valid UUID."
        )

    room = db.query(models.Room).filter(models.Room.id == room_uuid).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.get("/{room_id}/with-hotel", response_model=schemas.RoomWithHotel)
def get_room_with_hotel(room_id: str, db: Session = Depends(database.get_db)):
    try:
        # Validate that room_id is a valid UUID
        room_uuid = UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid room ID format. Must be a valid UUID."
        )

    room = db.query(models.Room).filter(models.Room.id == room_uuid).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.post("/hotels/{hotel_id}/", response_model=schemas.Room)
def create_room(
    hotel_id: str, room: schemas.RoomCreate, db: Session = Depends(database.get_db)
):
    try:
        # Validate that hotel_id is a valid UUID
        hotel_uuid = UUID(hotel_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid hotel ID format. Must be a valid UUID."
        )

    # Verificar que el hotel existe
    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_uuid).first()
    if hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")

    db_room = models.Room(
        hotel_id=hotel_uuid,
        name=room.name,
        description=room.description,
        price=room.price,
        images=room.images,
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room
