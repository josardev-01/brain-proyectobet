"""expand live snapshot metrics

Revision ID: c3f9d2704a12
Revises: b81c4e3a90ad
Create Date: 2026-09-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3f9d2704a12"
down_revision: Union[str, None] = "b81c4e3a90ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_COLUMNS = (
    "shots_off_target_home", "shots_off_target_away",
    "attacks_home", "attacks_away",
    "dangerous_attacks_home", "dangerous_attacks_away",
    "yellow_cards_home", "yellow_cards_away",
)


def upgrade() -> None:
    with op.batch_alter_table("snapshots") as batch_op:
        for name in _COLUMNS:
            batch_op.add_column(sa.Column(name, sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("snapshots") as batch_op:
        for name in reversed(_COLUMNS):
            batch_op.drop_column(name)
