# Hyperfunnel 🏨

**Hyperfunnel** is a modern REST API built with FastAPI for comprehensive hotel, room, availability, and booking management. It provides a robust and scalable solution for hotel management systems.

## 🚀 Features

- **Complete REST API** for hotel management
- **PostgreSQL database** with SQLAlchemy ORM
- **Automatic migrations** with Alembic
- **Complete Dockerization** for easy deployment
- **Data validation** with Pydantic schemas
- **Automatic API documentation** with Swagger/OpenAPI
- **Real-time availability management**
- **Booking system** with booking states

## 🏗️ Architecture

The project is structured following FastAPI best practices:

```
app/
├── models/          # SQLAlchemy database models
├── schemas/         # Pydantic schemas for validation
├── routers/         # API endpoints
├── database.py      # Database configuration
└── main.py          # Main FastAPI application
```

## 🛠️ Technologies

- **Backend**: FastAPI (Python 3.8+)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
- **Containers**: Docker & Docker Compose
- **Dependency Management**: uv

## 📋 Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- PostgreSQL (optional, included in Docker)

## 🚀 Installation and Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd Hyperfunnel
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
POSTGRES_DB=hyperfunnel
POSTGRES_USER=hyperfunnel_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### 3. Run with Docker (Recommended)

```bash
# Build and run all services
docker-compose up --build

# Run in background
docker-compose up -d
```

### 4. Local Installation (Alternative)

```bash
# Install dependencies
uv sync

# Run migrations
alembic upgrade head

# Run the application
uv run uvicorn app.main:app --reload
```

## 🌐 API Endpoints

### Hotels
- `GET /hotels` - List all hotels
- `POST /hotels` - Create new hotel
- `GET /hotels/{hotel_id}` - Get specific hotel
- `PUT /hotels/{hotel_id}` - Update hotel
- `DELETE /hotels/{hotel_id}` - Delete hotel

### Rooms
- `GET /rooms` - List all rooms
- `POST /rooms` - Create new room
- `GET /rooms/{room_id}` - Get specific room
- `PUT /rooms/{room_id}` - Update room
- `DELETE /rooms/{room_id}` - Delete room

### Availability
- `GET /availability` - Query availability
- `POST /availability` - Set availability
- `PUT /availability/{availability_id}` - Update availability

### Bookings
- `GET /bookings` - List all bookings
- `POST /bookings` - Create new booking
- `GET /bookings/{booking_id}` - Get specific booking
- `PUT /bookings/{booking_id}` - Update booking
- `DELETE /bookings/{booking_id}` - Cancel booking

### Destinations
- `GET /destinations` - List available destinations

### Utilities
- `POST /seed` - Populate database with sample data

## 📖 API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🗄️ Database

### Main Models

- **Hotel**: Hotel information (name, address, stars, etc.)
- **Room**: Hotel rooms (type, capacity, price, etc.)
- **Availability**: Room availability by date
- **Booking**: Customer bookings with states

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Change description"

# Apply migrations
alembic upgrade head

# Revert migration
alembic downgrade -1
```

## 🧪 Testing

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app
```

## 🐳 Docker

### Build images

```bash
# Build API image
docker build -f Dockerfile.api -t hyperfunnel-api .

# Build PostgreSQL image
docker build -f Dockerfile.postgres -t hyperfunnel-postgres .
```

### Available services

- **API**: Port 8000
- **PostgreSQL**: Port 5432

## 📝 Usage

### Hotel creation example

```python
import requests

# Create new hotel
hotel_data = {
    "name": "Plaza Hotel",
    "address": "Main Street 123",
    "city": "Madrid",
    "country": "Spain",
    "stars": 4,
    "description": "Luxury hotel in downtown Madrid"
}

response = requests.post("http://localhost:8000/hotels", json=hotel_data)
print(response.json())
```

### Availability query example

```python
# Query availability
params = {
    "hotel_id": 1,
    "check_in": "2024-01-15",
    "check_out": "2024-01-17",
    "guests": 2
}

response = requests.get("http://localhost:8000/availability", params=params)
print(response.json())
```

## 🔧 Development

### Project structure

```
Hyperfunnel/
├── alembic/                 # Database migrations
├── app/                     # Application code
│   ├── models/             # SQLAlchemy models
│   ├── routers/            # API endpoints
│   ├── schemas/            # Pydantic schemas
│   ├── database.py         # Database configuration
│   └── main.py             # Main application
├── docker-compose.yml       # Docker configuration
├── Dockerfile.api          # API Dockerfile
├── Dockerfile.postgres     # PostgreSQL Dockerfile
├── pyproject.toml          # Project dependencies
└── README.md               # This file
```

### Adding new endpoints

1. Create new router in `app/routers/`
2. Define schemas in `app/schemas/`
3. Create models in `app/models/` if needed
4. Include the router in `app/main.py`

## 🚀 Deployment

### Production

```bash
# Build for production
docker-compose -f docker-compose.prod.yml up --build

# Use production environment variables
export NODE_ENV=production
docker-compose up -d
```

### Production environment variables

```env
POSTGRES_DB=hyperfunnel_prod
POSTGRES_USER=hyperfunnel_prod_user
POSTGRES_PASSWORD=very_secure_production_password
POSTGRES_HOST=your_production_db_host
POSTGRES_PORT=5432
```
