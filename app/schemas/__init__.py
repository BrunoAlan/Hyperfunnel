from .hotel import (
    Hotel,
    HotelBase,
    HotelCreate,
    HotelUpdate,
    HotelUpdateDB,
)
from .room import (
    Room,
    RoomBase,
    RoomCreate,
    RoomCreateWithHotel,
    RoomUpdate,
    RoomUpdateDB,
)
from .relationships import (
    HotelWithRooms,
    RoomWithHotel,
)
from .availability import (
    Availability,
    AvailabilityBase,
    AvailabilityCreate,
    AvailabilityUpdate,
    AvailabilityWithRoom,
    AvailabilityRange,
    AvailabilitySearch,
)
from .booking import (
    Booking,
    BookingCreate,
    BookingUpdate,
    BookingWithDetails,
)

__all__ = [
    # Hotel schemas
    "Hotel",
    "HotelBase",
    "HotelCreate",
    "HotelUpdate",
    "HotelUpdateDB",
    "HotelWithRooms",
    # Room schemas
    "Room",
    "RoomBase",
    "RoomCreate",
    "RoomCreateWithHotel",
    "RoomUpdate",
    "RoomUpdateDB",
    "RoomWithHotel",
    # Availability schemas
    "Availability",
    "AvailabilityBase",
    "AvailabilityCreate",
    "AvailabilityUpdate",
    "AvailabilityWithRoom",
    "AvailabilityRange",
    "AvailabilitySearch",
    # Booking schemas
    "Booking",
    "BookingCreate",
    "BookingUpdate",
    "BookingWithDetails",
]
