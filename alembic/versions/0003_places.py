"""Add places table with PostGIS geometry and GiST index.

Revision ID: 0003_places
Revises: 0002_trip_sessions
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0003_places"
down_revision: Union[str, None] = "0002_trip_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "places",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column(
            "geom",
            Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("country_code", sa.String(length=8), nullable=True),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_id", sa.String(length=128), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_places_geom",
        "places",
        ["geom"],
        postgresql_using="gist",
    )
    op.create_index("ix_places_country_code", "places", ["country_code"])
    op.create_index(
        "uq_places_provider_provider_id",
        "places",
        ["provider", "provider_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_places_provider_provider_id", table_name="places")
    op.drop_index("ix_places_country_code", table_name="places")
    op.drop_index("ix_places_geom", table_name="places")
    op.drop_table("places")
