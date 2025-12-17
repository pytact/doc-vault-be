"""Add name field to users

Revision ID: add_name_to_users
Revises: add_password_reset_fields
Create Date: 2025-01-20 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_name_to_users'
down_revision: Union[str, None] = 'add_password_reset_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add name column to users table
    op.add_column('users', sa.Column('name', sa.String(length=255), nullable=True))
    
    # Set default name from email for existing users (so they have a name value)
    op.execute("UPDATE users SET name = email WHERE name IS NULL")


def downgrade() -> None:
    # Remove name column
    op.drop_column('users', 'name')

