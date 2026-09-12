"""Add trip_sessions table for guest chat sessions.

Revision ID: 0002_trip_sessions
Revises: 0001_baseline
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_trip_sessions"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trip_sessions",
        sa.Column("session_id", sa.String(length=36), primary_key=True),
        sa.Column("guest_id", sa.String(length=36), nullable=False),
        sa.Column(
            "messages",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "budget",
            sa.String(length=32),
            nullable=False,
            server_default="dialogue",
        ),
        sa.Column("intent", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("trip_scope", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("hitl", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("catalog", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("itinerary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("validation", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("trip_id", sa.String(length=36), nullable=True),
        sa.Column("run", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("obs_trace_id", sa.Text(), nullable=True),
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
    op.create_index("ix_trip_sessions_guest_id", "trip_sessions", ["guest_id"])


def downgrade() -> None:
    op.drop_index("ix_trip_sessions_guest_id", table_name="trip_sessions")
    op.drop_table("trip_sessions")
