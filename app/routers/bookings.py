from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from uuid import UUID
from .. import database
from ..models import Booking, Hotel, Room
from ..schemas import (
    Booking as BookingSchema,
    BookingCreate,
    BookingUpdate,
    BookingWithDetails,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("", response_model=List[BookingSchema])
def get_bookings(db: Session = Depends(database.get_db)):
    """Get all bookings"""
    bookings = db.query(Booking).all()
    return bookings


@router.get("/{booking_id}", response_model=BookingSchema)
def get_booking(booking_id: str, db: Session = Depends(database.get_db)):
    """Get a specific booking by ID"""
    try:
        # Validate that booking_id is a valid UUID
        booking_uuid = UUID(booking_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid booking ID format. Must be a valid UUID."
        )

    booking = db.query(Booking).filter(Booking.booking_id == booking_uuid).first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    return booking


@router.get("/{booking_id}/details", response_model=BookingWithDetails)
def get_booking_with_details(booking_id: str, db: Session = Depends(database.get_db)):
    """Get a specific booking with hotel and room details"""
    try:
        # Validate that booking_id is a valid UUID
        booking_uuid = UUID(booking_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid booking ID format. Must be a valid UUID."
        )

    # Query booking with hotel and room details
    booking = (
        db.query(Booking)
        .options(joinedload(Booking.hotel_ref), joinedload(Booking.room_ref))
        .filter(Booking.booking_id == booking_uuid)
        .first()
    )

    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Create response with details
    booking_dict = {
        "booking_id": booking.booking_id,
        "hotel": booking.hotel,
        "room": booking.room,
        "price": booking.price,
        "status": booking.status,
        "created_at": booking.created_at,
        "updated_at": booking.updated_at,
        "hotel_name": booking.hotel_ref.name if booking.hotel_ref else None,
        "hotel_city": booking.hotel_ref.city if booking.hotel_ref else None,
        "hotel_country": booking.hotel_ref.country if booking.hotel_ref else None,
        "room_name": booking.room_ref.name if booking.room_ref else None,
        "room_description": booking.room_ref.description if booking.room_ref else None,
    }

    return BookingWithDetails(**booking_dict)


@router.post("", response_model=BookingSchema)
def create_booking(booking: BookingCreate, db: Session = Depends(database.get_db)):
    """Create a new booking"""
    # Validate that hotel exists
    hotel = db.query(Hotel).filter(Hotel.id == booking.hotel).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    # Validate that room exists and belongs to the hotel
    room = (
        db.query(Room)
        .filter(Room.id == booking.room, Room.hotel_id == booking.hotel)
        .first()
    )
    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found or does not belong to the specified hotel",
        )

    db_booking = Booking(
        hotel=booking.hotel,
        room=booking.room,
        price=booking.price,
        status=booking.status,
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    return db_booking


@router.put("/{booking_id}", response_model=BookingSchema)
def update_booking(
    booking_id: str, booking: BookingCreate, db: Session = Depends(database.get_db)
):
    """Update a booking completely"""
    try:
        # Validate that booking_id is a valid UUID
        booking_uuid = UUID(booking_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid booking ID format. Must be a valid UUID."
        )

    db_booking = db.query(Booking).filter(Booking.booking_id == booking_uuid).first()
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Validate that hotel exists
    hotel = db.query(Hotel).filter(Hotel.id == booking.hotel).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    # Validate that room exists and belongs to the hotel
    room = (
        db.query(Room)
        .filter(Room.id == booking.room, Room.hotel_id == booking.hotel)
        .first()
    )
    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found or does not belong to the specified hotel",
        )

    # Update all fields
    db_booking.hotel = booking.hotel
    db_booking.room = booking.room
    db_booking.price = booking.price
    db_booking.status = booking.status

    db.commit()
    db.refresh(db_booking)

    return db_booking


@router.patch("/{booking_id}", response_model=BookingSchema)
def partial_update_booking(
    booking_id: str, booking: BookingUpdate, db: Session = Depends(database.get_db)
):
    """Partially update a booking"""
    try:
        # Validate that booking_id is a valid UUID
        booking_uuid = UUID(booking_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid booking ID format. Must be a valid UUID."
        )

    db_booking = db.query(Booking).filter(Booking.booking_id == booking_uuid).first()
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Update only provided fields
    update_data = booking.model_dump(exclude_unset=True)

    # Validate hotel and room if they are being updated
    if "hotel" in update_data:
        hotel = db.query(Hotel).filter(Hotel.id == update_data["hotel"]).first()
        if not hotel:
            raise HTTPException(status_code=404, detail="Hotel not found")

    if "room" in update_data:
        # Get the hotel_id to validate the room
        hotel_id = update_data.get("hotel", db_booking.hotel)
        room = (
            db.query(Room)
            .filter(Room.id == update_data["room"], Room.hotel_id == hotel_id)
            .first()
        )
        if not room:
            raise HTTPException(
                status_code=404,
                detail="Room not found or does not belong to the specified hotel",
            )

    for field, value in update_data.items():
        setattr(db_booking, field, value)

    db.commit()
    db.refresh(db_booking)

    return db_booking


@router.delete("/{booking_id}")
def delete_booking(booking_id: str, db: Session = Depends(database.get_db)):
    """Delete a booking"""
    try:
        # Validate that booking_id is a valid UUID
        booking_uuid = UUID(booking_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid booking ID format. Must be a valid UUID."
        )

    db_booking = db.query(Booking).filter(Booking.booking_id == booking_uuid).first()
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    db.delete(db_booking)
    db.commit()

    return {"message": "Booking deleted successfully"}


@router.get("/by-hotel/{hotel_id}", response_model=List[BookingSchema])
def get_bookings_by_hotel(hotel_id: str, db: Session = Depends(database.get_db)):
    """Get all bookings for a specific hotel"""
    try:
        # Validate that hotel_id is a valid UUID
        hotel_uuid = UUID(hotel_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid hotel ID format. Must be a valid UUID."
        )

    # Validate that hotel exists
    hotel = db.query(Hotel).filter(Hotel.id == hotel_uuid).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    bookings = db.query(Booking).filter(Booking.hotel == hotel_uuid).all()
    return bookings


@router.get("/by-room/{room_id}", response_model=List[BookingSchema])
def get_bookings_by_room(room_id: str, db: Session = Depends(database.get_db)):
    """Get all bookings for a specific room"""
    try:
        # Validate that room_id is a valid UUID
        room_uuid = UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid room ID format. Must be a valid UUID."
        )

    # Validate that room exists
    room = db.query(Room).filter(Room.id == room_uuid).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    bookings = db.query(Booking).filter(Booking.room == room_uuid).all()
    return bookings
