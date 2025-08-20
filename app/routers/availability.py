from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import date, timedelta
from .. import database
from ..models import Availability, Room
from ..schemas import (
    Availability as AvailabilitySchema,
    AvailabilityCreate,
    AvailabilityUpdate,
    AvailabilityWithRoom,
    AvailabilityRange,
    AvailabilitySearch,
)

router = APIRouter(prefix="/availability", tags=["availability"])


@router.get("", response_model=List[AvailabilitySchema])
def get_availability(
    room_id: Optional[UUID] = Query(None, description="Filter by room ID"),
    check_in_date: Optional[date] = Query(None, description="Check-in date for range"),
    check_out_date: Optional[date] = Query(
        None, description="Check-out date for range"
    ),
    available_only: bool = Query(False, description="Show only available dates"),
    db: Session = Depends(database.get_db),
):
    """Get availability records with optional filters"""
    query = db.query(Availability)

    if room_id:
        query = query.filter(Availability.room_id == room_id)

    if check_in_date:
        query = query.filter(Availability.date >= check_in_date)

    if check_out_date:
        query = query.filter(Availability.date <= check_out_date)

    if available_only:
        query = query.filter(
            and_(
                Availability.available_rooms > 0,
                Availability.is_blocked == False,
            )
        )

    return query.order_by(Availability.date).all()


@router.get("/{availability_id}", response_model=AvailabilitySchema)
def get_availability_by_id(
    availability_id: str, db: Session = Depends(database.get_db)
):
    """Get a specific availability record by ID"""
    try:
        availability_uuid = UUID(availability_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid availability ID format. Must be a valid UUID.",
        )

    availability = (
        db.query(Availability).filter(Availability.id == availability_uuid).first()
    )

    if availability is None:
        raise HTTPException(status_code=404, detail="Availability record not found")

    return availability


@router.post("", response_model=AvailabilitySchema)
def create_availability(
    availability: AvailabilityCreate, db: Session = Depends(database.get_db)
):
    """Create a single availability record"""
    # Verify that the room exists
    room = db.query(Room).filter(Room.id == availability.room_id).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    # Check if availability already exists for this room and date
    existing = (
        db.query(Availability)
        .filter(
            and_(
                Availability.room_id == availability.room_id,
                Availability.date == availability.date,
            )
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Availability already exists for room {availability.room_id} on {availability.date}",
        )

    db_availability = Availability(**availability.model_dump())
    db.add(db_availability)
    db.commit()
    db.refresh(db_availability)

    return db_availability


@router.post("/range", response_model=List[AvailabilitySchema])
def create_availability_range(
    availability_range: AvailabilityRange,
    db: Session = Depends(database.get_db),
):
    """Create availability records for a date range"""
    # Verify that the room exists
    room = db.query(Room).filter(Room.id == availability_range.room_id).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    if availability_range.check_in_date > availability_range.check_out_date:
        raise HTTPException(
            status_code=400,
            detail="Check-in date must be before or equal to check-out date",
        )

    created_records = []
    current_date = availability_range.check_in_date

    while current_date <= availability_range.check_out_date:
        # Check if availability already exists for this room and date
        existing = (
            db.query(Availability)
            .filter(
                and_(
                    Availability.room_id == availability_range.room_id,
                    Availability.date == current_date,
                )
            )
            .first()
        )

        if not existing:
            db_availability = Availability(
                room_id=availability_range.room_id,
                date=current_date,
                total_rooms=availability_range.total_rooms,
                available_rooms=availability_range.available_rooms,
                price_override=availability_range.price_override,
                is_blocked=availability_range.is_blocked,
            )
            db.add(db_availability)
            created_records.append(db_availability)

        current_date += timedelta(days=1)

    db.commit()

    # Refresh all created records
    for record in created_records:
        db.refresh(record)

    return created_records


@router.put("/{availability_id}", response_model=AvailabilitySchema)
def update_availability(
    availability_id: str,
    availability_update: AvailabilityUpdate,
    db: Session = Depends(database.get_db),
):
    """Update an availability record"""
    try:
        availability_uuid = UUID(availability_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid availability ID format. Must be a valid UUID.",
        )

    db_availability = (
        db.query(Availability).filter(Availability.id == availability_uuid).first()
    )

    if db_availability is None:
        raise HTTPException(status_code=404, detail="Availability record not found")

    # Update only the provided fields
    update_data = availability_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_availability, field, value)

    db.commit()
    db.refresh(db_availability)

    return db_availability


@router.delete("/{availability_id}")
def delete_availability(availability_id: str, db: Session = Depends(database.get_db)):
    """Delete an availability record"""
    try:
        availability_uuid = UUID(availability_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid availability ID format. Must be a valid UUID.",
        )

    db_availability = (
        db.query(Availability).filter(Availability.id == availability_uuid).first()
    )

    if db_availability is None:
        raise HTTPException(status_code=404, detail="Availability record not found")

    db.delete(db_availability)
    db.commit()

    return {"message": "Availability record deleted successfully"}


@router.post("/search", response_model=List[AvailabilityWithRoom])
def search_availability(
    search_params: AvailabilitySearch, db: Session = Depends(database.get_db)
):
    """
    Search for available rooms based on criteria.

    This endpoint ensures that rooms are available for ALL days in the requested date range.
    A room will only be returned if it has availability records for every single day
    between check_in_date and check_out_date (inclusive).
    """

    # Calculate the number of days in the requested range
    days_needed = (search_params.check_out_date - search_params.check_in_date).days + 1

    # Base query to get availability records within the date range
    base_query = db.query(Availability).join(Room)

    # Filter by date range
    base_query = base_query.filter(
        and_(
            Availability.date >= search_params.check_in_date,
            Availability.date <= search_params.check_out_date,
        )
    )

    # Filter by minimum available rooms
    base_query = base_query.filter(
        Availability.available_rooms >= search_params.min_rooms
    )

    # Filter by not blocked
    base_query = base_query.filter(Availability.is_blocked == False)

    # Filter by hotel if provided
    if search_params.hotel_id:
        base_query = base_query.filter(Room.hotel_id == search_params.hotel_id)

    # Filter by room if provided
    if search_params.room_id:
        base_query = base_query.filter(Availability.room_id == search_params.room_id)

    # Get all availability records that meet the basic criteria
    all_records = base_query.all()

    # Group records by room_id to check if each room has availability for ALL days
    from collections import defaultdict

    rooms_by_id = defaultdict(list)

    for record in all_records:
        rooms_by_id[record.room_id].append(record)

    # Filter rooms that have availability for ALL days in the range
    valid_rooms = []
    for room_id, records in rooms_by_id.items():
        # Check if this room has records for all required days
        record_dates = {record.date for record in records}

        # Generate all dates in the requested range
        current_date = search_params.check_in_date
        required_dates = set()
        while current_date <= search_params.check_out_date:
            required_dates.add(current_date)
            current_date += timedelta(days=1)

        # If the room has availability for all required dates, include it
        if required_dates.issubset(record_dates):
            valid_rooms.extend(records)

    # Sort the valid records
    valid_rooms.sort(key=lambda x: (x.date, x.room.name))

    # Convert the records to properly format the room data
    result = []
    for record in valid_rooms:
        # Convert the record to dict and manually handle room conversion
        record_dict = {
            "id": record.id,
            "room_id": record.room_id,
            "date": record.date,
            "total_rooms": record.total_rooms,
            "available_rooms": record.available_rooms,
            "price_override": record.price_override,
            "is_blocked": record.is_blocked,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "room": {
                "id": record.room.id,
                "hotel_id": record.room.hotel_id,
                "name": record.room.name,
                "description": record.room.description,
                "price": record.room.price,
                "guest": record.room.guest,
                "images": getattr(record.room, "images_list", None),
                "amenities": getattr(record.room, "amenities_list", None),
                "created_at": record.room.created_at,
                "updated_at": record.room.updated_at,
            },
        }
        result.append(AvailabilityWithRoom.model_validate(record_dict))

    return result


@router.get("/room/{room_id}/calendar", response_model=List[AvailabilitySchema])
def get_room_calendar(
    room_id: str,
    check_in_date: date = Query(..., description="Check-in date for calendar"),
    check_out_date: date = Query(..., description="Check-out date for calendar"),
    db: Session = Depends(database.get_db),
):
    """Get availability calendar for a specific room"""
    try:
        room_uuid = UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid room ID format. Must be a valid UUID."
        )

    # Verify that the room exists
    room = db.query(Room).filter(Room.id == room_uuid).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    if check_in_date > check_out_date:
        raise HTTPException(
            status_code=400,
            detail="Check-in date must be before or equal to check-out date",
        )

    availability_records = (
        db.query(Availability)
        .filter(
            and_(
                Availability.room_id == room_uuid,
                Availability.date >= check_in_date,
                Availability.date <= check_out_date,
            )
        )
        .order_by(Availability.date)
        .all()
    )

    return availability_records


@router.post("/room/{room_id}/block-dates")
def block_dates(
    room_id: str,
    check_in_date: date = Query(..., description="Check-in date to block"),
    check_out_date: date = Query(..., description="Check-out date to block"),
    db: Session = Depends(database.get_db),
):
    """Block dates for a specific room (set is_blocked=True)"""
    try:
        room_uuid = UUID(room_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid room ID format. Must be a valid UUID."
        )

    # Verify that the room exists
    room = db.query(Room).filter(Room.id == room_uuid).first()
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    if check_in_date > check_out_date:
        raise HTTPException(
            status_code=400,
            detail="Check-in date must be before or equal to check-out date",
        )

    # Update existing records or create new ones as blocked
    current_date = check_in_date
    updated_count = 0
    created_count = 0

    while current_date <= check_out_date:
        existing = (
            db.query(Availability)
            .filter(
                and_(
                    Availability.room_id == room_uuid,
                    Availability.date == current_date,
                )
            )
            .first()
        )

        if existing:
            existing.is_blocked = True
            updated_count += 1
        else:
            db_availability = Availability(
                room_id=room_uuid,
                date=current_date,
                total_rooms=5,
                available_rooms=0,
                is_blocked=True,
            )
            db.add(db_availability)
            created_count += 1

        current_date += timedelta(days=1)

    db.commit()

    return {
        "message": f"Blocked dates from {check_in_date} to {check_out_date}",
        "updated_records": updated_count,
        "created_records": created_count,
        "total_blocked": updated_count + created_count,
    }
