"""Add trips table for reopenable draft artifacts.

Revision ID: 0004_trips
Revises: 0003_places
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_trips"
down_revision: Union[str, None] = "0003_places"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trips",
        sa.Column("trip_id", sa.String(length=36), primary_key=True),
        sa.Column("guest_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column(
            "itinerary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "validation",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "route_geometry",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_trips_guest_id", "trips", ["guest_id"])
    op.create_index("ix_trips_session_id", "trips", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_trips_session_id", table_name="trips")
    op.drop_index("ix_trips_guest_id", table_name="trips")
    op.drop_table("trips")
