"""add candidate stage

Revision ID: a2f4c9d1e7b3
Revises: c1b46297478b
"""
import sqlalchemy as sa
from alembic import op

revision = "a2f4c9d1e7b3"
down_revision = "c1b46297478b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("stage", sa.String(20), nullable=False, server_default="new"))


def downgrade() -> None:
    op.drop_column("candidates", "stage")
