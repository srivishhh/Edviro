"""create assets table

Revision ID: 20260901_000001
Revises: 
Create Date: 2026-09-01 00:00:01.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260901_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("asset_type", sa.String(length=50), nullable=False),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column("floor_id", sa.Integer(), nullable=True),
        sa.Column("manufacturer", sa.String(length=120), nullable=True),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("installation_date", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="healthy"),
        sa.Column("health_score", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_code"),
    )
    op.create_index(op.f("ix_assets_id"), "assets", ["id"], unique=False)
    op.create_index(op.f("ix_assets_asset_code"), "assets", ["asset_code"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_assets_asset_code"), table_name="assets")
    op.drop_index(op.f("ix_assets_id"), table_name="assets")
    op.drop_table("assets")
