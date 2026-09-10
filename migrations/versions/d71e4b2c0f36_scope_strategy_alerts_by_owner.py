"""scope strategy alerts by owner

Revision ID: d71e4b2c0f36
Revises: c3f9d2704a12
Create Date: 2026-09-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d71e4b2c0f36"
down_revision: Union[str, None] = "c3f9d2704a12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("matches") as batch:
        batch.add_column(sa.Column("home_odds", sa.Float(), nullable=True))
        batch.add_column(sa.Column("draw_odds", sa.Float(), nullable=True))
        batch.add_column(sa.Column("away_odds", sa.Float(), nullable=True))
        batch.add_column(sa.Column("home_probability", sa.Float(), nullable=True))
        batch.add_column(sa.Column("draw_probability", sa.Float(), nullable=True))
        batch.add_column(sa.Column("away_probability", sa.Float(), nullable=True))

    with op.batch_alter_table("strategies") as batch:
        batch.drop_constraint("uq_strategy_version", type_="unique")
        batch.create_unique_constraint(
            "uq_owner_strategy_version", ["owner_id", "strategy_key", "version"]
        )

    with op.batch_alter_table("alerts") as batch:
        batch.add_column(sa.Column("owner_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("strategy_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_alerts_owner_id_users", "users", ["owner_id"], ["id"], ondelete="CASCADE"
        )
        batch.create_foreign_key(
            "fk_alerts_strategy_id_strategies", "strategies", ["strategy_id"], ["id"],
            ondelete="SET NULL",
        )
        batch.create_index("ix_alerts_owner_id", ["owner_id"])
        batch.create_index("ix_alerts_strategy_id", ["strategy_id"])


def downgrade() -> None:
    with op.batch_alter_table("alerts") as batch:
        batch.drop_index("ix_alerts_strategy_id")
        batch.drop_index("ix_alerts_owner_id")
        batch.drop_constraint("fk_alerts_strategy_id_strategies", type_="foreignkey")
        batch.drop_constraint("fk_alerts_owner_id_users", type_="foreignkey")
        batch.drop_column("strategy_id")
        batch.drop_column("owner_id")

    with op.batch_alter_table("strategies") as batch:
        batch.drop_constraint("uq_owner_strategy_version", type_="unique")
        batch.create_unique_constraint("uq_strategy_version", ["strategy_key", "version"])

    with op.batch_alter_table("matches") as batch:
        batch.drop_column("away_probability")
        batch.drop_column("draw_probability")
        batch.drop_column("home_probability")
        batch.drop_column("away_odds")
        batch.drop_column("draw_odds")
        batch.drop_column("home_odds")
