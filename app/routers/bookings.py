from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List
from uuid import UUID
from datetime import date, timedelta
from .. import database
from ..models import Booking, Hotel, Room, Availability
from ..models.booking import BookingStatus
from ..schemas import (
    Booking as BookingSchema,
    BookingCreate,
    BookingUpdate,
    BookingWithDetails,
)
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/bookings", tags=["bookings"])


class BookingQuoteRequest(BaseModel):
    """Schema for requesting a booking quote"""

    room_id: UUID
    check_in_date: date = Field(..., description="Check-in date")
    check_out_date: date = Field(..., description="Check-out date")
    guests: int = Field(default=1, ge=1, le=10, description="Number of guests")

    @field_validator("check_out_date")
    @classmethod
    def validate_checkout_after_checkin(cls, v, info):
        if "check_in_date" in info.data and v <= info.data["check_in_date"]:
            raise ValueError("Check-out date must be after check-in date")
        return v

    @field_validator("check_in_date")
    @classmethod
    def validate_checkin_not_past(cls, v):
        if v < date.today():
            raise ValueError("Check-in date cannot be in the past")
        return v


# Utility functions for availability management
def check_room_availability(
    db: Session,
    room_id: UUID,
    check_in_date: date,
    check_out_date: date,
    guests: int = 1,
) -> bool:
    """
    Check if a room has enough availability for the requested dates.
    Returns True if available, False otherwise.
    """
    current_date = check_in_date
    while current_date < check_out_date:  # Note: check_out_date is exclusive
        availability = (
            db.query(Availability)
            .filter(
                and_(
                    Availability.room_id == room_id,
                    Availability.date == current_date,
                    Availability.available_rooms >= guests,
                    Availability.is_blocked == False,
                )
            )
            .first()
        )

        if not availability:
            return False

        current_date += timedelta(days=1)

    return True


def reserve_room_availability(
    db: Session,
    room_id: UUID,
    check_in_date: date,
    check_out_date: date,
    guests: int = 1,
) -> None:
    """
    Decrement available_rooms for the specified date range.
    Should only be called after check_room_availability returns True.
    """
    current_date = check_in_date
    while current_date < check_out_date:
        availability = (
            db.query(Availability)
            .filter(
                and_(
                    Availability.room_id == room_id,
                    Availability.date == current_date,
                )
            )
            .first()
        )

        if availability and availability.available_rooms >= guests:
            availability.available_rooms -= guests
        else:
            # This shouldn't happen if check_room_availability was called first
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reserve room for date {current_date}. This shouldn't happen.",
            )

        current_date += timedelta(days=1)


def release_room_availability(
    db: Session,
    room_id: UUID,
    check_in_date: date,
    check_out_date: date,
    guests: int = 1,
) -> None:
    """
    Increment available_rooms for the specified date range.
    Used when canceling a booking.
    """
    current_date = check_in_date
    while current_date < check_out_date:
        availability = (
            db.query(Availability)
            .filter(
                and_(
                    Availability.room_id == room_id,
                    Availability.date == current_date,
                )
            )
            .first()
        )

        if availability:
            availability.available_rooms += guests

        current_date += timedelta(days=1)


def calculate_booking_price(
    db: Session, room_id: UUID, check_in_date: date, check_out_date: date
) -> float:
    """
    Calculate the total price for a booking based on room rates and availability overrides.
    Returns the total price for all nights.
    """
    total_price = 0.0
    current_date = check_in_date

    # Get the room to access base price
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    while current_date < check_out_date:  # check_out_date is exclusive
        # Check if there's a price override for this specific date
        availability = (
            db.query(Availability)
            .filter(
                and_(
                    Availability.room_id == room_id,
                    Availability.date == current_date,
                )
            )
            .first()
        )

        # Use price override if available, otherwise use room's base price
        if availability and availability.price_override is not None:
            daily_price = availability.price_override
        else:
            daily_price = room.price

        total_price += daily_price
        current_date += timedelta(days=1)

    return total_price


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
        "hotel_id": booking.hotel_id,
        "room_id": booking.room_id,
        "check_in_date": booking.check_in_date,
        "check_out_date": booking.check_out_date,
        "guests": booking.guests,
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
    """Create a new booking with automatic availability management"""
    # Validate that hotel exists
    hotel = db.query(Hotel).filter(Hotel.id == booking.hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    # Validate that room exists and belongs to the hotel
    room = (
        db.query(Room)
        .filter(Room.id == booking.room_id, Room.hotel_id == booking.hotel_id)
        .first()
    )
    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found or does not belong to the specified hotel",
        )

    # Check availability for the requested dates and guests
    if not check_room_availability(
        db,
        booking.room_id,
        booking.check_in_date,
        booking.check_out_date,
        booking.guests,
    ):
        raise HTTPException(
            status_code=409,
            detail=f"Room not available for the requested dates ({booking.check_in_date} to {booking.check_out_date}) for {booking.guests} guests",
        )

    # Calculate price automatically if not provided
    calculated_price = booking.price
    if calculated_price is None:
        calculated_price = calculate_booking_price(
            db, booking.room_id, booking.check_in_date, booking.check_out_date
        )

    try:
        # Reserve the room by decrementing availability
        reserve_room_availability(
            db,
            booking.room_id,
            booking.check_in_date,
            booking.check_out_date,
            booking.guests,
        )

        # Create the booking
        db_booking = Booking(
            hotel_id=booking.hotel_id,
            room_id=booking.room_id,
            check_in_date=booking.check_in_date,
            check_out_date=booking.check_out_date,
            guests=booking.guests,
            price=calculated_price,
            status=booking.status,
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)

        return db_booking

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create booking: {str(e)}"
        )


@router.put("/{booking_id}", response_model=BookingSchema)
def update_booking(
    booking_id: str, booking: BookingCreate, db: Session = Depends(database.get_db)
):
    """Update a booking completely with availability management"""
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

    # Store original booking data for availability restoration
    original_room = db_booking.room_id
    original_check_in = db_booking.check_in_date
    original_check_out = db_booking.check_out_date
    original_guests = db_booking.guests

    # Validate that hotel exists
    hotel = db.query(Hotel).filter(Hotel.id == booking.hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    # Validate that room exists and belongs to the hotel
    room = (
        db.query(Room)
        .filter(Room.id == booking.room_id, Room.hotel_id == booking.hotel_id)
        .first()
    )
    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found or does not belong to the specified hotel",
        )

    # Check if we need to update availability (dates, room, or guests changed)
    availability_changed = (
        original_room != booking.room_id
        or original_check_in != booking.check_in_date
        or original_check_out != booking.check_out_date
        or original_guests != booking.guests
    )

    if availability_changed:
        # Check availability for new dates/room/guests
        if not check_room_availability(
            db,
            booking.room_id,
            booking.check_in_date,
            booking.check_out_date,
            booking.guests,
        ):
            raise HTTPException(
                status_code=409,
                detail=f"Room not available for the new dates ({booking.check_in_date} to {booking.check_out_date}) for {booking.guests} guests",
            )

    # Calculate price automatically if not provided or if relevant details changed
    calculated_price = booking.price
    if calculated_price is None or availability_changed:
        calculated_price = calculate_booking_price(
            db, booking.room_id, booking.check_in_date, booking.check_out_date
        )

    try:
        if availability_changed:
            # Release availability for original booking
            release_room_availability(
                db,
                original_room,
                original_check_in,
                original_check_out,
                original_guests,
            )

            # Reserve availability for new booking
            reserve_room_availability(
                db,
                booking.room_id,
                booking.check_in_date,
                booking.check_out_date,
                booking.guests,
            )

        # Update all fields
        db_booking.hotel_id = booking.hotel_id
        db_booking.room_id = booking.room_id
        db_booking.check_in_date = booking.check_in_date
        db_booking.check_out_date = booking.check_out_date
        db_booking.guests = booking.guests
        db_booking.price = calculated_price
        db_booking.status = booking.status

        db.commit()
        db.refresh(db_booking)

        return db_booking

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update booking: {str(e)}"
        )


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
    if "hotel_id" in update_data:
        hotel = db.query(Hotel).filter(Hotel.id == update_data["hotel_id"]).first()
        if not hotel:
            raise HTTPException(status_code=404, detail="Hotel not found")

    if "room_id" in update_data:
        # Get the hotel_id to validate the room
        hotel_id = update_data.get("hotel_id", db_booking.hotel_id)
        room = (
            db.query(Room)
            .filter(Room.id == update_data["room_id"], Room.hotel_id == hotel_id)
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


@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: str, db: Session = Depends(database.get_db)):
    """Cancel a booking and restore room availability"""
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

    # Check if booking is already cancelled
    if db_booking.status.value == "cancelled":
        raise HTTPException(status_code=400, detail="Booking is already cancelled")

    try:
        # Restore room availability
        release_room_availability(
            db,
            db_booking.room_id,
            db_booking.check_in_date,
            db_booking.check_out_date,
            db_booking.guests,
        )

        # Update booking status to cancelled
        db_booking.status = BookingStatus.CANCELLED

        db.commit()
        db.refresh(db_booking)

        return {
            "message": "Booking cancelled successfully",
            "booking_id": str(db_booking.booking_id),
            "restored_availability": f"Restored {db_booking.guests} rooms for dates {db_booking.check_in_date} to {db_booking.check_out_date}",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to cancel booking: {str(e)}"
        )


@router.post("/{booking_id}/checkout")
def checkout_booking(booking_id: str, db: Session = Depends(database.get_db)):
    """Fake checkout - Confirm a booking by changing status from PENDING to CONFIRMED"""
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

    # Check if booking is in PENDING status
    if db_booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Booking cannot be confirmed. Current status: {db_booking.status.value}. Only PENDING bookings can be confirmed.",
        )

    try:
        # Update booking status to confirmed
        db_booking.status = BookingStatus.CONFIRMED

        db.commit()
        db.refresh(db_booking)

        return {
            "message": "Booking confirmed successfully",
            "booking_id": str(db_booking.booking_id),
            "status": db_booking.status.value,
            "check_in_date": db_booking.check_in_date,
            "check_out_date": db_booking.check_out_date,
            "guests": db_booking.guests,
            "total_price": db_booking.price,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to confirm booking: {str(e)}"
        )


@router.post("/quote")
def get_booking_quote(
    quote_request: BookingQuoteRequest,
    db: Session = Depends(database.get_db),
):
    """Get a price quote for a booking without creating it"""

    # Validate room exists
    room = db.query(Room).filter(Room.id == quote_request.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Check availability
    if not check_room_availability(
        db,
        quote_request.room_id,
        quote_request.check_in_date,
        quote_request.check_out_date,
        quote_request.guests,
    ):
        raise HTTPException(
            status_code=409,
            detail=f"Room not available for the requested dates ({quote_request.check_in_date} to {quote_request.check_out_date}) for {quote_request.guests} guests",
        )

    # Calculate price
    total_price = calculate_booking_price(
        db,
        quote_request.room_id,
        quote_request.check_in_date,
        quote_request.check_out_date,
    )
    nights = (quote_request.check_out_date - quote_request.check_in_date).days

    # Get price breakdown by date
    price_breakdown = []
    current_date = quote_request.check_in_date
    while current_date < quote_request.check_out_date:
        availability = (
            db.query(Availability)
            .filter(
                and_(
                    Availability.room_id == quote_request.room_id,
                    Availability.date == current_date,
                )
            )
            .first()
        )

        daily_price = (
            availability.price_override
            if availability and availability.price_override
            else room.price
        )
        price_breakdown.append(
            {
                "date": current_date,
                "price": daily_price,
                "is_special_rate": availability
                and availability.price_override is not None,
            }
        )
        current_date += timedelta(days=1)

    return {
        "room_id": quote_request.room_id,
        "room_name": room.name,
        "check_in_date": quote_request.check_in_date,
        "check_out_date": quote_request.check_out_date,
        "guests": quote_request.guests,
        "nights": nights,
        "total_price": total_price,
        "average_price_per_night": total_price / nights if nights > 0 else 0,
        "price_breakdown": price_breakdown,
        "currency": "USD",  # You might want to make this configurable
        "availability_confirmed": True,
    }


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

    bookings = db.query(Booking).filter(Booking.hotel_id == hotel_uuid).all()
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

    bookings = db.query(Booking).filter(Booking.room_id == room_uuid).all()
    return bookings


class BookingQuoteRequest(BaseModel):
    """Schema for requesting a booking quote"""

    room_id: UUID
    check_in_date: date = Field(..., description="Check-in date")
    check_out_date: date = Field(..., description="Check-out date")
    guests: int = Field(default=1, ge=1, le=10, description="Number of guests")

    @field_validator("check_out_date")
    @classmethod
    def validate_checkout_after_checkin(cls, v, info):
        if "check_in_date" in info.data and v <= info.data["check_in_date"]:
            raise ValueError("Check-out date must be after check-in date")
        return v

    @field_validator("check_in_date")
    @classmethod
    def validate_checkin_not_past(cls, v):
        if v < date.today():
            raise ValueError("Check-in date cannot be in the past")
        return v
