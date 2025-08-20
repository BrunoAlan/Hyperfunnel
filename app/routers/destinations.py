from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.models.hotel import Hotel
from .. import database


router = APIRouter(prefix="/destinations", tags=["destinations"])


@router.get("")
def get_hotels(db: Session = Depends(database.get_db)):
    hotels = db.query(Hotel).all()

    return list(set([hotel.country for hotel in hotels]))
