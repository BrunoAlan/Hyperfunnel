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


@router.get("/", response_model=List[AvailabilitySchema])
def get_availability(
    room_id: Optional[UUID] = Query(None, description="Filter by room ID"),
    start_date: Optional[date] = Query(None, description="Start date for range"),
    end_date: Optional[date] = Query(None, description="End date for range"),
    available_only: bool = Query(False, description="Show only available dates"),
    db: Session = Depends(database.get_db),
):
    """Get availability records with optional filters"""
    query = db.query(Availability)

    if room_id:
        query = query.filter(Availability.room_id == room_id)

    if start_date:
        query = query.filter(Availability.date >= start_date)

    if end_date:
        query = query.filter(Availability.date <= end_date)

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


@router.post("/", response_model=AvailabilitySchema)
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

    if availability_range.start_date > availability_range.end_date:
        raise HTTPException(
            status_code=400, detail="Start date must be before or equal to end date"
        )

    created_records = []
    current_date = availability_range.start_date

    while current_date <= availability_range.end_date:
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
    """Search for available rooms based on criteria"""
    query = db.query(Availability).join(Room)

    # Filter by date range
    query = query.filter(
        and_(
            Availability.date >= search_params.start_date,
            Availability.date <= search_params.end_date,
        )
    )

    # Filter by minimum available rooms
    query = query.filter(Availability.available_rooms >= search_params.min_rooms)

    # Filter by not blocked
    query = query.filter(Availability.is_blocked == False)

    # Filter by hotel if provided
    if search_params.hotel_id:
        query = query.filter(Room.hotel_id == search_params.hotel_id)

    # Filter by room if provided
    if search_params.room_id:
        query = query.filter(Availability.room_id == search_params.room_id)

    availability_records = query.order_by(Availability.date, Room.name).all()

    return availability_records


@router.get("/room/{room_id}/calendar", response_model=List[AvailabilitySchema])
def get_room_calendar(
    room_id: str,
    start_date: date = Query(..., description="Start date for calendar"),
    end_date: date = Query(..., description="End date for calendar"),
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

    if start_date > end_date:
        raise HTTPException(
            status_code=400, detail="Start date must be before or equal to end date"
        )

    availability_records = (
        db.query(Availability)
        .filter(
            and_(
                Availability.room_id == room_uuid,
                Availability.date >= start_date,
                Availability.date <= end_date,
            )
        )
        .order_by(Availability.date)
        .all()
    )

    return availability_records


@router.post("/room/{room_id}/block-dates")
def block_dates(
    room_id: str,
    start_date: date = Query(..., description="Start date to block"),
    end_date: date = Query(..., description="End date to block"),
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

    if start_date > end_date:
        raise HTTPException(
            status_code=400, detail="Start date must be before or equal to end date"
        )

    # Update existing records or create new ones as blocked
    current_date = start_date
    updated_count = 0
    created_count = 0

    while current_date <= end_date:
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
        "message": f"Blocked dates from {start_date} to {end_date}",
        "updated_records": updated_count,
        "created_records": created_count,
    }
