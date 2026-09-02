"""facility models

Revision ID: 20260901_000002
Revises: 20260901_000001
Create Date: 2026-09-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_000002"
down_revision = "20260901_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "buildings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_buildings_code"), "buildings", ["code"], unique=True)
    op.create_index(op.f("ix_buildings_id"), "buildings", ["id"], unique=False)

    op.create_table(
        "floors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("building_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("floor_number", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_floors_building_id"), "floors", ["building_id"], unique=False)
    op.create_index(op.f("ix_floors_id"), "floors", ["id"], unique=False)
    op.create_foreign_key(None, "floors", "buildings", ["building_id"], ["id"])

    op.create_foreign_key(None, "assets", "buildings", ["building_id"], ["id"])
    op.create_foreign_key(None, "assets", "floors", ["floor_id"], ["id"])

    op.create_table(
        "sensors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sensor_code", sa.String(length=80), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("sensor_type", sa.String(length=80), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=True),
        sa.Column("normal_min", sa.Float(), nullable=True),
        sa.Column("normal_max", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="online"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sensor_code"),
    )
    op.create_index(op.f("ix_sensors_asset_id"), "sensors", ["asset_id"], unique=False)
    op.create_index(op.f("ix_sensors_id"), "sensors", ["id"], unique=False)
    op.create_index(op.f("ix_sensors_sensor_code"), "sensors", ["sensor_code"], unique=True)
    op.create_foreign_key(None, "sensors", "assets", ["asset_id"], ["id"])

    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sensor_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sensor_readings_id"), "sensor_readings", ["id"], unique=False)
    op.create_index(op.f("ix_sensor_readings_sensor_id"), "sensor_readings", ["sensor_id"], unique=False)
    op.create_index(op.f("ix_sensor_readings_timestamp"), "sensor_readings", ["timestamp"], unique=False)
    op.create_index("ix_sensor_readings_sensor_timestamp", "sensor_readings", ["sensor_id", "timestamp"], unique=False)
    op.create_foreign_key(None, "sensor_readings", "sensors", ["sensor_id"], ["id"])

    op.create_table(
        "asset_relationships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_asset_id", sa.Integer(), nullable=False),
        sa.Column("relationship_type", sa.String(length=60), nullable=False),
        sa.Column("target_asset_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_asset_relationships_id"), "asset_relationships", ["id"], unique=False)
    op.create_foreign_key(None, "asset_relationships", "assets", ["source_asset_id"], ["id"])
    op.create_foreign_key(None, "asset_relationships", "assets", ["target_asset_id"], ["id"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("alert_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False, server_default="WARNING"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("anomaly_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("detected_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="OPEN"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_alert_type"), "alerts", ["alert_type"], unique=False)
    op.create_index(op.f("ix_alerts_asset_id"), "alerts", ["asset_id"], unique=False)
    op.create_index(op.f("ix_alerts_detected_at"), "alerts", ["detected_at"], unique=False)
    op.create_index(op.f("ix_alerts_id"), "alerts", ["id"], unique=False)
    op.create_foreign_key(None, "alerts", "assets", ["asset_id"], ["id"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("asset_relationships")
    op.drop_table("sensor_readings")
    op.drop_table("sensors")
    op.drop_table("floors")
    op.drop_table("buildings")

