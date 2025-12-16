"""Fix user_roles unique constraint

Revision ID: fix_user_roles_constraint
Revises: 5ca5439930b6
Create Date: 2025-12-15 07:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'fix_user_roles_constraint'
down_revision: Union[str, None] = '5ca5439930b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix unique constraint on user_roles table.
    
    Clean up duplicate roles and create proper unique constraints:
    1. One role per user per family (for family-scoped roles)
    2. One superadmin role per user (for global superadmin roles)
    """
    # First, clean up any existing duplicate roles
    # For each (user_id, family_id) combination with multiple active roles,
    # keep only the most recent one (by created_at) and soft-delete the others
    op.execute("""
        WITH ranked_roles AS (
            SELECT 
                id,
                user_id,
                family_id,
                ROW_NUMBER() OVER (
                    PARTITION BY user_id, COALESCE(family_id::text, 'NULL')
                    ORDER BY created_at DESC
                ) as rn
            FROM user_roles
            WHERE deleted_at IS NULL AND is_del = false
        )
        UPDATE user_roles ur
        SET 
            is_del = true,
            deleted_at = NOW(),
            updated_at = NOW()
        FROM ranked_roles rr
        WHERE ur.id = rr.id 
            AND rr.rn > 1
            AND ur.deleted_at IS NULL
            AND ur.is_del = false;
    """)
    
    # Drop the old incorrect unique index (if it exists)
    op.execute("DROP INDEX IF EXISTS uq_user_roles_user_active;")
    
    # Create new unique index for family roles: (user_id, family_id) where family_id IS NOT NULL
    op.create_index(
        'uq_user_roles_user_family_active',
        'user_roles',
        ['user_id', 'family_id'],
        unique=True,
        postgresql_where=text("deleted_at IS NULL AND family_id IS NOT NULL")
    )
    
    # Create new unique index for superadmin roles: user_id where family_id IS NULL
    op.create_index(
        'uq_user_roles_superadmin_active',
        'user_roles',
        ['user_id'],
        unique=True,
        postgresql_where=text("deleted_at IS NULL AND family_id IS NULL")
    )


def downgrade() -> None:
    """Revert to the old unique constraint."""
    # Drop the new indexes
    op.drop_index('uq_user_roles_superadmin_active', table_name='user_roles')
    op.drop_index('uq_user_roles_user_family_active', table_name='user_roles')
    
    # Restore the old unique index
    op.create_index(
        'uq_user_roles_user_active',
        'user_roles',
        ['user_id'],
        unique=True,
        postgresql_where=text("deleted_at IS NULL")
    )

