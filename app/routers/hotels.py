from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from .. import models, database, schemas

router = APIRouter(prefix="/hotels", tags=["hotels"])


@router.get("/", response_model=List[schemas.Hotel])
def get_hotels(db: Session = Depends(database.get_db)):
    hotels = db.query(models.Hotel).all()
    # Convert each hotel to use the images_list property
    for hotel in hotels:
        if hasattr(hotel, "images_list"):
            hotel.images = hotel.images_list
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

    # Convert images JSON string to list for API response
    if hasattr(hotel, "images_list"):
        hotel.images = hotel.images_list

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

    # Convert images JSON string to list for API response
    if hasattr(hotel, "images_list"):
        hotel.images = hotel.images_list

    return hotel


@router.post("/", response_model=schemas.Hotel)
def create_hotel(hotel: schemas.HotelCreate, db: Session = Depends(database.get_db)):
    # Convert images list to JSON string for storage
    images_json = None
    if hotel.images:
        import json

        images_json = json.dumps(hotel.images)

    db_hotel = models.Hotel(
        name=hotel.name,
        country=hotel.country,
        city=hotel.city,
        stars=hotel.stars,
        images=images_json,
    )
    db.add(db_hotel)
    db.commit()
    db.refresh(db_hotel)

    # Convert images back to list for API response
    if hasattr(db_hotel, "images_list"):
        db_hotel.images = db_hotel.images_list

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

    # Convert images list to JSON string for storage
    images_json = None
    if hotel.images:
        import json

        images_json = json.dumps(hotel.images)

    # Update all fields
    db_hotel.name = hotel.name
    db_hotel.country = hotel.country
    db_hotel.city = hotel.city
    db_hotel.stars = hotel.stars
    db_hotel.images = images_json

    db.commit()
    db.refresh(db_hotel)

    # Convert images back to list for API response
    if hasattr(db_hotel, "images_list"):
        db_hotel.images = db_hotel.images_list

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

    # Handle images conversion if provided
    if "images" in update_data and update_data["images"] is not None:
        import json

        update_data["images"] = json.dumps(update_data["images"])

    for field, value in update_data.items():
        setattr(db_hotel, field, value)

    db.commit()
    db.refresh(db_hotel)

    # Convert images back to list for API response
    if hasattr(db_hotel, "images_list"):
        db_hotel.images = db_hotel.images_list

    return db_hotel
