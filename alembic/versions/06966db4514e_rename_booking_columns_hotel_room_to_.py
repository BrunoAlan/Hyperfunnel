"""rename_booking_columns_hotel_room_to_hotel_id_room_id

Revision ID: 06966db4514e
Revises: ad43ba410fec
Create Date: 2025-08-20 17:51:32.371171

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "06966db4514e"
down_revision: Union[str, Sequence[str], None] = "ad43ba410fec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename columns in bookings table
    op.alter_column("bookings", "hotel", new_column_name="hotel_id")
    op.alter_column("bookings", "room", new_column_name="room_id")


def downgrade() -> None:
    """Downgrade schema."""
    # Revert column names in bookings table
    op.alter_column("bookings", "hotel_id", new_column_name="hotel")
    op.alter_column("bookings", "room_id", new_column_name="room")
