"""initial migration

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("balance", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.CheckConstraint("balance >= 0", name="non_negative_balance"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "markets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column(
            "status",
            sa.Enum("open", "closed", "resolved", "cancelled", name="marketstatus"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("outcome", sa.Enum("yes", "no", name="outcomeside"), nullable=True),
        sa.Column("yes_shares", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("no_shares", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("yes_price", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("no_price", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("closes_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_markets_creator_id"), nullable=True),
        sa.CheckConstraint("yes_shares > 0", name="positive_yes_shares"),
        sa.CheckConstraint("no_shares > 0", name="positive_no_shares"),
    )
    op.create_index("ix_markets_id", "markets", ["id"])

    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_positions_user_id"), nullable=False),
        sa.Column("market_id", sa.Integer(), sa.ForeignKey("markets.id", name="fk_positions_market_id"), nullable=False),
        sa.Column("side", sa.Enum("yes", "no", name="outcomeside"), nullable=False),
        sa.Column("shares", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_price", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_cost", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_winner", sa.Boolean(), nullable=True),
        sa.Column("payout", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "market_id", "side", name="uq_positions_user_market_side"),
        sa.CheckConstraint("shares >= 0", name="non_negative_shares"),
    )
    op.create_index("ix_positions_id", "positions", ["id"])
    op.create_index("ix_positions_user_id", "positions", ["user_id"])
    op.create_index("ix_positions_market_id", "positions", ["market_id"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_transactions_user_id"), nullable=False),
        sa.Column("market_id", sa.Integer(), sa.ForeignKey("markets.id", name="fk_transactions_market_id"), nullable=True),
        sa.Column(
            "type",
            sa.Enum("buy", "sell", "deposit", "withdrawal", "payout", name="transactiontype"),
            nullable=False,
        ),
        sa.Column("side", sa.Enum("yes", "no", name="outcomeside"), nullable=True),
        sa.Column("shares", sa.Float(), nullable=True),
        sa.Column("price_per_share", sa.Float(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("balance_before", sa.Float(), nullable=False),
        sa.Column("balance_after", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_transactions_id", "transactions", ["id"])
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("positions")
    op.drop_table("markets")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS marketstatus")
    op.execute("DROP TYPE IF EXISTS outcomeside")
    op.execute("DROP TYPE IF EXISTS transactiontype")
