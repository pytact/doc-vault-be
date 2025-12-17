"""Add file_size and mime_type to documents

Revision ID: add_file_size_mime_type
Revises: add_taxonomy_relationships
Create Date: 2025-01-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_file_size_mime_type'
down_revision: Union[str, None] = 'add_taxonomy_relationships'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add file_size column to documents table
    op.add_column('documents', sa.Column('file_size', sa.Integer(), nullable=True))
    
    # Add mime_type column to documents table
    op.add_column('documents', sa.Column('mime_type', sa.String(length=100), nullable=True))


def downgrade() -> None:
    # Remove mime_type column
    op.drop_column('documents', 'mime_type')
    
    # Remove file_size column
    op.drop_column('documents', 'file_size')

