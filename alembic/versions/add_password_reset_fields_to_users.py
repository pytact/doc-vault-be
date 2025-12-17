"""Add password reset fields to users

Revision ID: add_password_reset_fields
Revises: 6b6957a34f15
Create Date: 2025-01-20 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_password_reset_fields'
down_revision: Union[str, None] = '6b6957a34f15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add reset_token column to users table
    op.add_column('users', sa.Column('reset_token', sa.String(length=255), nullable=True))
    
    # Add reset_token_sent_at column to users table
    op.add_column('users', sa.Column('reset_token_sent_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add reset_token_expires_at column to users table
    op.add_column('users', sa.Column('reset_token_expires_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove reset_token_expires_at column
    op.drop_column('users', 'reset_token_expires_at')
    
    # Remove reset_token_sent_at column
    op.drop_column('users', 'reset_token_sent_at')
    
    # Remove reset_token column
    op.drop_column('users', 'reset_token')

