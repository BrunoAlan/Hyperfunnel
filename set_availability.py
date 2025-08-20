"""
Script to make all rooms available during the entire month of September 2025.

This script:
1. Gets all existing rooms from the database
2. Generates availability records for each day of September 2025
3. Sets total availability for each room type
4. Handles existing records by updating or creating new ones as needed

Usage:
    python set_availability.py
"""

import asyncio
from datetime import date, timedelta
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal, engine
from app.models import Room, Availability
import calendar

# Configuration for September 2025
YEAR = 2025
MONTH = 9  # September
DEFAULT_TOTAL_ROOMS = 5
DEFAULT_AVAILABLE_ROOMS = 5


def get_db() -> Session:
    """Get database session"""
    return SessionLocal()


def get_september_dates(year: int, month: int) -> List[date]:
    """Generate all dates for the month of September 2025"""
    # Get the number of days in September for the given year
    _, days_in_month = calendar.monthrange(year, month)

    dates = []
    for day in range(1, days_in_month + 1):
        dates.append(date(year, month, day))

    return dates


def get_all_rooms(db: Session) -> List[Room]:
    """Get all rooms from the database"""
    rooms = db.query(Room).all()
    return rooms


def create_or_update_availability(
    db: Session,
    room_id: str,
    target_date: date,
    total_rooms: int = DEFAULT_TOTAL_ROOMS,
    available_rooms: int = DEFAULT_AVAILABLE_ROOMS,
    is_blocked: bool = False,
) -> bool:
    """
    Create or update an availability record for a room on a specific date.

    Returns:
        bool: True if a new record was created, False if an existing one was updated
    """
    # Check if a record already exists for this room and date
    existing_availability = (
        db.query(Availability)
        .filter(Availability.room_id == room_id, Availability.date == target_date)
        .first()
    )

    if existing_availability:
        # Update existing record
        existing_availability.total_rooms = total_rooms
        existing_availability.available_rooms = available_rooms
        existing_availability.is_blocked = is_blocked
        # Don't modify price_override to maintain existing special prices
        return False
    else:
        # Create new record
        new_availability = Availability(
            room_id=room_id,
            date=target_date,
            total_rooms=total_rooms,
            available_rooms=available_rooms,
            is_blocked=is_blocked,
            price_override=None,  # No special price by default
        )
        db.add(new_availability)
        return True


def set_september_availability():
    """Main function to configure September 2025 availability"""
    db = get_db()

    try:
        print("🏨 Setting up availability for September 2025")
        print("=" * 60)

        # 1. Get all rooms
        print("📋 Getting rooms from database...")
        rooms = get_all_rooms(db)

        if not rooms:
            print("❌ No rooms found in the database.")
            print("   Make sure rooms exist before running this script.")
            return

        print(f"✅ Found {len(rooms)} rooms:")
        for room in rooms:
            print(f"   - {room.name} (ID: {room.id}) - €{room.price}/night")

        # 2. Generate September 2025 dates
        print(f"\n📅 Generating dates for September {YEAR}...")
        september_dates = get_september_dates(YEAR, MONTH)
        print(f"✅ Generated {len(september_dates)} dates:")
        print(f"   From {september_dates[0]} to {september_dates[-1]}")

        # 3. Configure availability for each room and date
        print(f"\n🔧 Setting up availability...")
        total_records = len(rooms) * len(september_dates)
        created_count = 0
        updated_count = 0

        for room in rooms:
            print(f"\n   Processing: {room.name}")
            room_created = 0
            room_updated = 0

            for target_date in september_dates:
                is_new = create_or_update_availability(
                    db=db,
                    room_id=room.id,
                    target_date=target_date,
                    total_rooms=DEFAULT_TOTAL_ROOMS,
                    available_rooms=DEFAULT_AVAILABLE_ROOMS,
                    is_blocked=False,
                )

                if is_new:
                    created_count += 1
                    room_created += 1
                else:
                    updated_count += 1
                    room_updated += 1

            print(f"     ✓ Created: {room_created} | Updated: {room_updated}")

        # 4. Commit changes to database
        print(f"\n💾 Saving changes to database...")
        db.commit()

        # 5. Final summary
        print(f"\n✅ Availability configured successfully!")
        print(f"📊 Summary:")
        print(f"   • Rooms processed: {len(rooms)}")
        print(f"   • Dates configured: {len(september_dates)} days")
        print(f"   • Total records: {total_records}")
        print(f"   • New records created: {created_count}")
        print(f"   • Records updated: {updated_count}")
        print(f"   • Available rooms per day: {DEFAULT_AVAILABLE_ROOMS}")
        print(f"   • Total rooms per type: {DEFAULT_TOTAL_ROOMS}")

        print(f"\n🎯 Configuration applied:")
        print(f"   • Period: All of September {YEAR}")
        print(f"   • Status: All rooms available")
        print(f"   • No blocks: ✓")
        print(f"   • Special prices: Existing ones maintained")

    except Exception as e:
        print(f"\n❌ Error during configuration: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_availability():
    """Function to verify that availability was configured correctly"""
    db = get_db()

    try:
        print(f"\n🔍 Verifying configuration...")

        # Count availability records for September 2025
        september_start = date(YEAR, MONTH, 1)
        september_end = date(YEAR, MONTH, 30)

        availability_count = (
            db.query(Availability)
            .filter(
                Availability.date >= september_start, Availability.date <= september_end
            )
            .count()
        )

        room_count = db.query(Room).count()
        expected_records = room_count * 30  # 30 days in September

        print(f"📈 Verification statistics:")
        print(f"   • Availability records in September: {availability_count}")
        print(f"   • Expected records: {expected_records}")
        print(
            f"   • Status: {'✅ Correct' if availability_count == expected_records else '❌ Incomplete'}"
        )

        # Verify there are no blocked dates
        blocked_count = (
            db.query(Availability)
            .filter(
                Availability.date >= september_start,
                Availability.date <= september_end,
                Availability.is_blocked == True,
            )
            .count()
        )

        print(
            f"   • Blocked dates: {blocked_count} {'✅' if blocked_count == 0 else '⚠️'}"
        )

        # Verify total availability
        unavailable_count = (
            db.query(Availability)
            .filter(
                Availability.date >= september_start,
                Availability.date <= september_end,
                Availability.available_rooms == 0,
            )
            .count()
        )

        print(
            f"   • Dates without availability: {unavailable_count} {'✅' if unavailable_count == 0 else '⚠️'}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    try:
        # Execute main configuration
        set_september_availability()

        # Verify everything is correct
        verify_availability()

        print(f"\n🎉 Script completed successfully!")
        print(f"\n📝 Suggested next steps:")
        print(f"   1. Review availability using the API: GET /availability/")
        print(f"   2. Configure special prices if needed")
        print(f"   3. Adjust availability for specific dates if required")

    except KeyboardInterrupt:
        print(f"\n⚠️  Script interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
