"""add user approval workflow

Revision ID: b81c4e3a90ad
Revises: 6e278b374478
Create Date: 2026-09-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b81c4e3a90ad"
down_revision: Union[str, None] = "6e278b374478"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("role", sa.String(length=20), server_default="USER", nullable=False)
        )
        batch_op.add_column(
            sa.Column(
                "approval_status",
                sa.String(length=20),
                server_default="PENDING",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("reviewed_by_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_users_reviewed_by_id_users",
            "users",
            ["reviewed_by_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_users_approval_status", ["approval_status"], unique=False)
    op.execute("UPDATE users SET approval_status = 'APPROVED'")


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_approval_status")
        batch_op.drop_constraint("fk_users_reviewed_by_id_users", type_="foreignkey")
        batch_op.drop_column("reviewed_by_id")
        batch_op.drop_column("reviewed_at")
        batch_op.drop_column("approval_status")
        batch_op.drop_column("role")
