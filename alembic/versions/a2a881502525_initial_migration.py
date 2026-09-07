"""Initial migration

Revision ID: a2a881502525
Revises:
Create Date: 2026-09-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a2a881502525"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users must exist before tables that reference them.
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("quota_limit", sa.Integer(), nullable=True),
        sa.Column("quota_used", sa.Integer(), nullable=True),
        sa.Column("preferences", sa.JSON(), nullable=True),
        sa.Column("password_updated_at", sa.DateTime(), nullable=True),
        sa.Column("resend_count", sa.Integer(), nullable=True),
        sa.Column("last_resend_at", sa.DateTime(), nullable=True),
        sa.Column("security_resend_count", sa.Integer(), nullable=True),
        sa.Column("security_last_resend_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("phone_number"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_phone_number", "users", ["phone_number"], unique=True)

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=True),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("total_requests", sa.Integer(), nullable=True),
        sa.Column("request_limit", sa.Integer(), nullable=True),
        sa.Column("ip_whitelist", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_api_keys_id", "api_keys", ["id"], unique=False)
    op.create_index("ix_api_keys_key", "api_keys", ["key"], unique=True)

    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("province", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("postal_code", sa.String(), nullable=True),
        sa.Column("rajaongkir_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_cities_id", "cities", ["id"], unique=False)
    op.create_index("ix_cities_name", "cities", ["name"], unique=True)

    op.create_table(
        "couriers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_couriers_id", "couriers", ["id"], unique=False)

    op.create_table(
        "subdistricts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("city_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subdistricts_id", "subdistricts", ["id"], unique=False)

    op.create_table(
        "tracking",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("awb", sa.String(), nullable=True),
        sa.Column("courier_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("origin_city_id", sa.Integer(), nullable=True),
        sa.Column("destination_city_id", sa.Integer(), nullable=True),
        sa.Column("service_type", sa.String(), nullable=True),
        sa.Column("weight_gram", sa.Integer(), nullable=True),
        sa.Column("length_cm", sa.Integer(), nullable=True),
        sa.Column("width_cm", sa.Integer(), nullable=True),
        sa.Column("height_cm", sa.Integer(), nullable=True),
        sa.Column("insurance_value", sa.Float(), nullable=True),
        sa.Column("shipping_cost", sa.Float(), nullable=True),
        sa.Column("sender_name", sa.String(), nullable=True),
        sa.Column("sender_phone", sa.String(), nullable=True),
        sa.Column("sender_address", sa.String(), nullable=True),
        sa.Column("sender_postal_code", sa.String(), nullable=True),
        sa.Column("sender_lat", sa.Float(), nullable=True),
        sa.Column("sender_long", sa.Float(), nullable=True),
        sa.Column("receiver_name", sa.String(), nullable=True),
        sa.Column("receiver_phone", sa.String(), nullable=True),
        sa.Column("receiver_address", sa.String(), nullable=True),
        sa.Column("receiver_postal_code", sa.String(), nullable=True),
        sa.Column("receiver_lat", sa.Float(), nullable=True),
        sa.Column("receiver_long", sa.Float(), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.Column("history", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["courier_id"], ["couriers.id"]),
        sa.ForeignKeyConstraint(["origin_city_id"], ["cities.id"]),
        sa.ForeignKeyConstraint(["destination_city_id"], ["cities.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("awb"),
    )
    op.create_index("ix_tracking_id", "tracking", ["id"], unique=False)
    op.create_index("ix_tracking_awb", "tracking", ["awb"], unique=True)

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("api_key_id", sa.Integer(), nullable=True),
        sa.Column("order_id", sa.String(), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=True),
        sa.Column("quota_added", sa.Integer(), nullable=True),
        sa.Column("payment_method", sa.String(), nullable=True),
        sa.Column("tx_metadata", sa.JSON(), nullable=True),
        sa.Column("tx_hash", sa.String(), nullable=True),
        sa.Column("actual_crypto_amount", sa.Float(), nullable=True),
        sa.Column("actual_saldo", sa.Numeric(15, 2), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("status_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["api_key_id"], ["api_keys.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
    )
    op.create_index("ix_transactions_id", "transactions", ["id"], unique=False)
    op.create_index("ix_transactions_order_id", "transactions", ["order_id"], unique=True)
    op.create_index("ix_transactions_tx_hash", "transactions", ["tx_hash"], unique=False)

    op.create_table(
        "verification_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("channel", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("is_used", sa.Boolean(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verification_codes_id", "verification_codes", ["id"], unique=False)

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("jti", sa.String(), nullable=True),
        sa.Column("device_info", sa.String(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_active", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jti"),
    )
    op.create_index("ix_user_sessions_id", "user_sessions", ["id"], unique=False)
    op.create_index("ix_user_sessions_jti", "user_sessions", ["jti"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_sessions_jti", table_name="user_sessions")
    op.drop_index("ix_user_sessions_id", table_name="user_sessions")
    op.drop_table("user_sessions")

    op.drop_index("ix_verification_codes_id", table_name="verification_codes")
    op.drop_table("verification_codes")

    op.drop_index("ix_transactions_tx_hash", table_name="transactions")
    op.drop_index("ix_transactions_order_id", table_name="transactions")
    op.drop_index("ix_transactions_id", table_name="transactions")
    op.drop_table("transactions")

    op.drop_index("ix_tracking_awb", table_name="tracking")
    op.drop_index("ix_tracking_id", table_name="tracking")
    op.drop_table("tracking")

    op.drop_index("ix_subdistricts_id", table_name="subdistricts")
    op.drop_table("subdistricts")

    op.drop_index("ix_couriers_id", table_name="couriers")
    op.drop_table("couriers")

    op.drop_index("ix_cities_name", table_name="cities")
    op.drop_index("ix_cities_id", table_name="cities")
    op.drop_table("cities")

    op.drop_index("ix_api_keys_key", table_name="api_keys")
    op.drop_index("ix_api_keys_id", table_name="api_keys")
    op.drop_table("api_keys")

    op.drop_index("ix_users_phone_number", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
