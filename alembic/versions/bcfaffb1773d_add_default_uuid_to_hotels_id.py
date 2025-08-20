"""add_default_uuid_to_hotels_id

Revision ID: bcfaffb1773d
Revises: 9ecc6ce4071c
Create Date: 2025-08-20 10:08:38.198985

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bcfaffb1773d"
down_revision: Union[str, Sequence[str], None] = "9ecc6ce4071c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add default value for hotels.id column
    op.execute("ALTER TABLE hotels ALTER COLUMN id SET DEFAULT uuid_generate_v4();")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove default value from hotels.id column
    op.execute("ALTER TABLE hotels ALTER COLUMN id DROP DEFAULT;")
