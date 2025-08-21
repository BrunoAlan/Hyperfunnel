"""
Script to make all rooms available during a specified month and year.

This script:
1. Gets all existing rooms from the database
2. Generates availability records for each day of the specified month and year
3. Sets total availability for each room type
4. Handles existing records by updating or creating new ones as needed

Usage:
    python set_availability.py --year 2025 --month 9 --total-rooms 5 --available-rooms 5
    python set_availability.py -y 2025 -m 9 -t 5 -a 5
    
    Default values:
    - year: current year
    - month: current month
    - total-rooms: 5
    - available-rooms: 5
"""

import asyncio
import argparse
from datetime import date, timedelta, datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal, engine
from app.models import Room, Availability
import calendar

# Default configuration values
DEFAULT_TOTAL_ROOMS = 5
DEFAULT_AVAILABLE_ROOMS = 5


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Set availability for rooms in a specified month and year"
    )

    # Get current year and month as defaults
    current_date = datetime.now()

    parser.add_argument(
        "--year",
        "-y",
        type=int,
        default=current_date.year,
        help=f"Year to set availability for (default: {current_date.year})",
    )

    parser.add_argument(
        "--month",
        "-m",
        type=int,
        default=current_date.month,
        choices=range(1, 13),
        help=f"Month to set availability for, 1-12 (default: {current_date.month})",
    )

    parser.add_argument(
        "--total-rooms",
        "-t",
        type=int,
        default=DEFAULT_TOTAL_ROOMS,
        help=f"Total number of rooms available per day (default: {DEFAULT_TOTAL_ROOMS})",
    )

    parser.add_argument(
        "--available-rooms",
        "-a",
        type=int,
        default=DEFAULT_AVAILABLE_ROOMS,
        help=f"Number of available rooms per day (default: {DEFAULT_AVAILABLE_ROOMS})",
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify the configuration after setting availability",
    )

    return parser.parse_args()


def get_db() -> Session:
    """Get database session"""
    return SessionLocal()


def get_month_dates(year: int, month: int) -> List[date]:
    """Generate all dates for the specified month and year"""
    # Get the number of days in the specified month for the given year
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


def set_month_availability(
    year: int, month: int, total_rooms: int, available_rooms: int
):
    """Main function to configure availability for the specified month and year"""
    db = get_db()

    try:
        month_name = calendar.month_name[month]
        print(f"🏨 Setting up availability for {month_name} {year}")
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

        # 2. Generate dates for the specified month and year
        print(f"\n📅 Generating dates for {month_name} {year}...")
        month_dates = get_month_dates(year, month)
        print(f"✅ Generated {len(month_dates)} dates:")
        print(f"   From {month_dates[0]} to {month_dates[-1]}")

        # 3. Configure availability for each room and date
        print(f"\n🔧 Setting up availability...")
        total_records = len(rooms) * len(month_dates)
        created_count = 0
        updated_count = 0

        for room in rooms:
            print(f"\n   Processing: {room.name}")
            room_created = 0
            room_updated = 0

            for target_date in month_dates:
                is_new = create_or_update_availability(
                    db=db,
                    room_id=room.id,
                    target_date=target_date,
                    total_rooms=total_rooms,
                    available_rooms=available_rooms,
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
        print(f"   • Dates configured: {len(month_dates)} days")
        print(f"   • Total records: {total_records}")
        print(f"   • New records created: {created_count}")
        print(f"   • Records updated: {updated_count}")
        print(f"   • Available rooms per day: {available_rooms}")
        print(f"   • Total rooms per type: {total_rooms}")

        print(f"\n🎯 Configuration applied:")
        print(f"   • Period: All of {month_name} {year}")
        print(f"   • Status: All rooms available")
        print(f"   • No blocks: ✓")
        print(f"   • Special prices: Existing ones maintained")

    except Exception as e:
        print(f"\n❌ Error during configuration: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_availability(year: int, month: int):
    """Function to verify that availability was configured correctly"""
    db = get_db()

    try:
        month_name = calendar.month_name[month]
        print(f"\n🔍 Verifying configuration for {month_name} {year}...")

        # Count availability records for the specified month and year
        month_check_in = date(year, month, 1)
        _, days_in_month = calendar.monthrange(year, month)
        month_check_out = date(year, month, days_in_month)

        availability_count = (
            db.query(Availability)
            .filter(
                Availability.date >= month_check_in,
                Availability.date <= month_check_out,
            )
            .count()
        )

        room_count = db.query(Room).count()
        expected_records = room_count * days_in_month

        print(f"📈 Verification statistics:")
        print(f"   • Availability records in {month_name} {year}: {availability_count}")
        print(f"   • Expected records: {expected_records}")
        print(
            f"   • Status: {'✅ Correct' if availability_count == expected_records else '❌ Incomplete'}"
        )

        # Verify there are no blocked dates
        blocked_count = (
            db.query(Availability)
            .filter(
                Availability.date >= month_check_in,
                Availability.date <= month_check_out,
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
                Availability.date >= month_check_in,
                Availability.date <= month_check_out,
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
        # Parse command line arguments
        args = parse_arguments()

        # Validate arguments
        if args.available_rooms > args.total_rooms:
            print("❌ Error: Available rooms cannot be greater than total rooms")
            exit(1)

        if args.available_rooms < 0 or args.total_rooms < 0:
            print("❌ Error: Room counts cannot be negative")
            exit(1)

        # Execute main configuration
        set_month_availability(
            year=args.year,
            month=args.month,
            total_rooms=args.total_rooms,
            available_rooms=args.available_rooms,
        )

        # Verify everything is correct if requested
        if args.verify:
            verify_availability(year=args.year, month=args.month)

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
