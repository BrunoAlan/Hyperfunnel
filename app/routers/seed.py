from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import delete
from typing import Dict, Any
from datetime import datetime, date
from .. import database
from ..models import Hotel, Room, Availability, Booking
import json
import os
import uuid

router = APIRouter(prefix="/seed", tags=["seed"])


@router.get("/export", response_model=Dict[str, Any])
def export_current_data(db: Session = Depends(database.get_db)):
    """
    Export all current data from the database to create a seed file.
    This captures hotels, rooms, and availability as they exist now.
    """
    try:
        # Get all hotels
        hotels = db.query(Hotel).all()
        hotels_data = []
        for hotel in hotels:
            hotel_dict = {
                "id": str(hotel.id),
                "name": hotel.name,
                "country": hotel.country,
                "city": hotel.city,
                "stars": hotel.stars,
                "images": hotel.images,
                "created_at": (
                    hotel.created_at.isoformat() if hotel.created_at else None
                ),
                "updated_at": (
                    hotel.updated_at.isoformat() if hotel.updated_at else None
                ),
            }
            hotels_data.append(hotel_dict)

        # Get all rooms
        rooms = db.query(Room).all()
        rooms_data = []
        for room in rooms:
            room_dict = {
                "id": str(room.id),
                "hotel_id": str(room.hotel_id),
                "name": room.name,
                "description": room.description,
                "price": room.price,
                "images": room.images,
                "amenities": room.amenities,
                "created_at": room.created_at.isoformat() if room.created_at else None,
                "updated_at": room.updated_at.isoformat() if room.updated_at else None,
            }
            rooms_data.append(room_dict)

        # Get all availability
        availability_records = db.query(Availability).all()
        availability_data = []
        for avail in availability_records:
            avail_dict = {
                "id": str(avail.id),
                "room_id": str(avail.room_id),
                "date": avail.date.isoformat(),
                "total_rooms": avail.total_rooms,
                "available_rooms": avail.available_rooms,
                "price_override": avail.price_override,
                "is_blocked": avail.is_blocked,
                "created_at": (
                    avail.created_at.isoformat() if avail.created_at else None
                ),
                "updated_at": (
                    avail.updated_at.isoformat() if avail.updated_at else None
                ),
            }
            availability_data.append(avail_dict)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hyperfunnel_seed_{timestamp}.json"
        file_path = os.path.join(os.getcwd(), filename)

        export_data = {
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "total_hotels": len(hotels_data),
                "total_rooms": len(rooms_data),
                "total_availability_records": len(availability_data),
                "file_created": filename,
            },
            "hotels": hotels_data,
            "rooms": rooms_data,
            "availability": availability_data,
        }

        # Save to JSON file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        except Exception as file_error:
            raise HTTPException(
                status_code=500,
                detail=f"Error creating file {filename}: {str(file_error)}",
            )

        return {
            "message": "Data exported successfully",
            "file_info": {
                "filename": filename,
                "file_path": file_path,
                "file_size_bytes": os.path.getsize(file_path),
            },
            "summary": export_data["export_info"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")


@router.post("/import", response_model=Dict[str, Any])
def import_seed_data(filename: str, db: Session = Depends(database.get_db)):
    """
    Import data from a previously exported seed file.
    This will clear all existing data and replace it with the data from the seed file.
    """
    try:
        # Check if file exists
        file_path = os.path.join(os.getcwd(), filename)
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404, detail=f"Seed file '{filename}' not found"
            )

        # Read and parse the seed file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                seed_data = json.load(f)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid JSON in seed file: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error reading seed file: {str(e)}"
            )

        # Validate seed file structure
        required_keys = ["hotels", "rooms", "availability"]
        for key in required_keys:
            if key not in seed_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid seed file format: missing '{key}' section",
                )

        # Start transaction to ensure data consistency
        try:
            # Clear existing data in correct order (due to foreign key constraints)
            # First clear availability (references rooms)
            db.execute(delete(Availability))
            # Then clear bookings (references rooms)
            db.execute(delete(Booking))
            # Then clear rooms (references hotels)
            db.execute(delete(Room))
            # Finally clear hotels
            db.execute(delete(Hotel))

            # Flush to ensure deletions are committed before inserts
            db.flush()

            # Import hotels
            hotels_imported = 0
            for hotel_data in seed_data["hotels"]:
                hotel = Hotel(
                    id=uuid.UUID(hotel_data["id"]),
                    name=hotel_data["name"],
                    country=hotel_data["country"],
                    city=hotel_data["city"],
                    stars=hotel_data["stars"],
                    images=hotel_data["images"],
                    created_at=(
                        datetime.fromisoformat(hotel_data["created_at"])
                        if hotel_data["created_at"]
                        else None
                    ),
                    updated_at=(
                        datetime.fromisoformat(hotel_data["updated_at"])
                        if hotel_data["updated_at"]
                        else None
                    ),
                )
                db.add(hotel)
                hotels_imported += 1

            # Flush hotels before adding rooms
            db.flush()

            # Import rooms
            rooms_imported = 0
            for room_data in seed_data["rooms"]:
                room = Room(
                    id=uuid.UUID(room_data["id"]),
                    hotel_id=uuid.UUID(room_data["hotel_id"]),
                    name=room_data["name"],
                    description=room_data["description"],
                    price=room_data["price"],
                    images=room_data["images"],
                    amenities=room_data["amenities"],
                    created_at=(
                        datetime.fromisoformat(room_data["created_at"])
                        if room_data["created_at"]
                        else None
                    ),
                    updated_at=(
                        datetime.fromisoformat(room_data["updated_at"])
                        if room_data["updated_at"]
                        else None
                    ),
                )
                db.add(room)
                rooms_imported += 1

            # Flush rooms before adding availability
            db.flush()

            # Import availability
            availability_imported = 0
            for avail_data in seed_data["availability"]:
                availability = Availability(
                    id=uuid.UUID(avail_data["id"]),
                    room_id=uuid.UUID(avail_data["room_id"]),
                    date=date.fromisoformat(avail_data["date"]),
                    total_rooms=avail_data["total_rooms"],
                    available_rooms=avail_data["available_rooms"],
                    price_override=avail_data["price_override"],
                    is_blocked=avail_data["is_blocked"],
                    created_at=(
                        datetime.fromisoformat(avail_data["created_at"])
                        if avail_data["created_at"]
                        else None
                    ),
                    updated_at=(
                        datetime.fromisoformat(avail_data["updated_at"])
                        if avail_data["updated_at"]
                        else None
                    ),
                )
                db.add(availability)
                availability_imported += 1

            # Commit all changes
            db.commit()

            return {
                "message": "Seed data imported successfully",
                "summary": {
                    "filename": filename,
                    "hotels_imported": hotels_imported,
                    "rooms_imported": rooms_imported,
                    "availability_records_imported": availability_imported,
                    "imported_at": datetime.now().isoformat(),
                },
            }

        except Exception as db_error:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Database error during import: {str(db_error)}"
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected error during import: {str(e)}"
        )


@router.post("/reset", response_model=Dict[str, Any])
def reset_to_seed_state(db: Session = Depends(database.get_db)):
    """
    Reset the database to the latest seed file state.
    This will look for the most recent seed file and import it.
    """
    try:
        # Find the most recent seed file
        seed_files = []
        for filename in os.listdir(os.getcwd()):
            if filename.startswith("hyperfunnel_seed_") and filename.endswith(".json"):
                seed_files.append(filename)

        if not seed_files:
            raise HTTPException(
                status_code=404,
                detail="No seed files found. Please export data first or provide a seed file.",
            )

        # Sort by filename (which contains timestamp) to get the most recent
        latest_seed_file = sorted(seed_files)[-1]

        # Import the latest seed file
        return import_seed_data(latest_seed_file, db)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error finding or importing seed file: {str(e)}"
        )
