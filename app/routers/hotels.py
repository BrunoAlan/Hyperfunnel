from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from .. import models, database, schemas

router = APIRouter(prefix="/hotels", tags=["hotels"])


@router.get("/", response_model=List[schemas.Hotel])
def get_hotels(db: Session = Depends(database.get_db)):
    hotels = db.query(models.Hotel).all()
    return hotels


@router.get("/{hotel_id}", response_model=schemas.Hotel)
def get_hotel(hotel_id: str, db: Session = Depends(database.get_db)):
    try:
        # Validate that hotel_id is a valid UUID
        hotel_uuid = UUID(hotel_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid hotel ID format. Must be a valid UUID."
        )

    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_uuid).first()
    if hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return hotel


@router.get("/{hotel_id}/with-rooms", response_model=schemas.HotelWithRooms)
def get_hotel_with_rooms(hotel_id: str, db: Session = Depends(database.get_db)):
    try:
        # Validate that hotel_id is a valid UUID
        hotel_uuid = UUID(hotel_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid hotel ID format. Must be a valid UUID."
        )

    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_uuid).first()
    if hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return hotel


@router.post("/", response_model=schemas.Hotel)
def create_hotel(hotel: schemas.HotelCreate, db: Session = Depends(database.get_db)):
    db_hotel = models.Hotel(
        name=hotel.name, country=hotel.country, city=hotel.city, stars=hotel.stars
    )
    db.add(db_hotel)
    db.commit()
    db.refresh(db_hotel)
    return db_hotel


@router.put("/{hotel_id}", response_model=schemas.Hotel)
def update_hotel(
    hotel_id: str, hotel: schemas.HotelCreate, db: Session = Depends(database.get_db)
):
    try:
        # Validate that hotel_id is a valid UUID
        hotel_uuid = UUID(hotel_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid hotel ID format. Must be a valid UUID."
        )

    db_hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_uuid).first()
    if db_hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")

    # Update all fields
    db_hotel.name = hotel.name
    db_hotel.country = hotel.country
    db_hotel.city = hotel.city
    db_hotel.stars = hotel.stars
    db_hotel.images = hotel.images

    db.commit()
    db.refresh(db_hotel)
    return db_hotel


@router.patch("/{hotel_id}", response_model=schemas.Hotel)
def partial_update_hotel(
    hotel_id: str, hotel: schemas.HotelUpdate, db: Session = Depends(database.get_db)
):
    try:
        # Validate that hotel_id is a valid UUID
        hotel_uuid = UUID(hotel_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid hotel ID format. Must be a valid UUID."
        )

    db_hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_uuid).first()
    if db_hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")

    # Update only provided fields
    update_data = hotel.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_hotel, field, value)

    db.commit()
    db.refresh(db_hotel)
    return db_hotel


@router.get("/{hotel_id}/rooms/", response_model=List[schemas.Room])
def get_hotel_rooms(hotel_id: str, db: Session = Depends(database.get_db)):
    try:
        # Validate that hotel_id is a valid UUID
        hotel_uuid = UUID(hotel_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid hotel ID format. Must be a valid UUID."
        )

    hotel = db.query(models.Hotel).filter(models.Hotel.id == hotel_uuid).first()
    if hotel is None:
        raise HTTPException(status_code=404, detail="Hotel not found")

    rooms = db.query(models.Room).filter(models.Room.hotel_id == hotel_uuid).all()
    return rooms
