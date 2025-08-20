from fastapi import FastAPI
from . import models, database
from .database import engine
from .routers import hotels, rooms

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Include routers
app.include_router(hotels.router)
app.include_router(rooms.router)


@app.get("/")
def read_root():
    return {"message": "Hyper funnel api"}
