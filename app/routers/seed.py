from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
from .. import database
from ..models import Hotel, Room, Availability
import json
import os

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
