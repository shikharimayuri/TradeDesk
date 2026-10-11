"""Initial schema baseline."""

from alembic import op
import sqlalchemy as sa

revision = "7d42513f42d2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("theme", sa.String(10), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "trades",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("trade_time", sa.Time(), nullable=True),
        sa.Column("followed_plan", sa.Boolean(), nullable=False),
        sa.Column("is_profit", sa.Boolean(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("trades")
    op.drop_table("users")