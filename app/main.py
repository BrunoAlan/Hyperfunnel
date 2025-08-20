from fastapi import FastAPI
from . import database
from .database import engine, Base
from .routers import hotels, rooms, availability, seed

# Import models to register them with SQLAlchemy
from .models import Hotel, Room, Availability  # noqa: F401

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(redirect_slashes=False)

# Include routers
app.include_router(hotels.router)
app.include_router(rooms.router)
app.include_router(availability.router)
app.include_router(seed.router)


@app.get("/")
def read_root():
    return {"message": "Hyper funnel api"}
