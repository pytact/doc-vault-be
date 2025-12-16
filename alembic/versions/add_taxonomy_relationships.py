"""Add taxonomy relationships

Revision ID: add_taxonomy_relationships
Revises: fb1597937ba5
Create Date: 2025-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_taxonomy_relationships'
down_revision: Union[str, None] = 'fb1597937ba5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Taxonomy relationships migration.
    
    Note: This migration is for documentation purposes only.
    The categories and subcategories tables already exist from the initial migration.
    The relationships (Category.subcategories and Subcategory.category) are ORM-level
    only and do not require database schema changes. They are defined in the models
    for SQLAlchemy relationship navigation.
    
    No database changes are needed as:
    - categories table already exists (from initial migration)
    - subcategories table already exists (from initial migration)
    - Foreign key constraint (category_id -> categories.id) already exists
    - Relationships are Python ORM mappings, not database schema elements
    """
    # No database changes needed - relationships are ORM-level only
    pass


def downgrade() -> None:
    """
    No changes to revert - relationships are ORM-level only.
    """
    # No database changes to revert
    pass

