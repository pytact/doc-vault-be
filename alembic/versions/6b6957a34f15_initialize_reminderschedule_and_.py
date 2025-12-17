"""Initialize ReminderSchedule and InAppNotification

Revision ID: 6b6957a34f15
Revises: add_file_size_mime_type
Create Date: 2025-12-17 05:13:51.227754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '6b6957a34f15'
down_revision: Union[str, None] = 'add_file_size_mime_type'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create reminder_schedules table
    op.create_table(
        'reminder_schedules',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('reminder_type', sa.String(length=10), nullable=False),
        sa.Column('send_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='RESTRICT', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("reminder_type IN ('30d', '7d', '0d')", name='ck_reminder_schedules_reminder_type_valid'),
        sa.CheckConstraint("status IN ('pending', 'sent', 'cancelled')", name='ck_reminder_schedules_status_valid')
    )
    
    # Create indexes for reminder_schedules
    op.create_index(op.f('ix_reminder_schedules_id'), 'reminder_schedules', ['id'], unique=False)
    op.create_index(op.f('ix_reminder_schedules_document_id'), 'reminder_schedules', ['document_id'], unique=False)
    op.create_index(op.f('ix_reminder_schedules_user_id'), 'reminder_schedules', ['user_id'], unique=False)
    op.create_index(op.f('ix_reminder_schedules_reminder_type'), 'reminder_schedules', ['reminder_type'], unique=False)
    op.create_index(op.f('ix_reminder_schedules_send_at'), 'reminder_schedules', ['send_at'], unique=False)
    op.create_index(op.f('ix_reminder_schedules_status'), 'reminder_schedules', ['status'], unique=False)
    op.create_index(op.f('ix_reminder_schedules_created_at'), 'reminder_schedules', ['created_at'], unique=False)
    op.create_index(op.f('ix_reminder_schedules_updated_at'), 'reminder_schedules', ['updated_at'], unique=False)
    
    # Create partial unique index for pending schedules
    op.create_index(
        'uq_reminder_schedules_document_user_type_pending',
        'reminder_schedules',
        ['document_id', 'user_id', 'reminder_type'],
        unique=True,
        postgresql_where=text("status = 'pending'")
    )
    
    # Create in_app_notifications table
    op.create_table(
        'in_app_notifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('reminder_type', sa.String(length=10), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_del', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='RESTRICT', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("reminder_type IN ('30d', '7d', '0d')", name='ck_in_app_notifications_reminder_type_valid')
    )
    
    # Create indexes for in_app_notifications
    op.create_index(op.f('ix_in_app_notifications_id'), 'in_app_notifications', ['id'], unique=False)
    op.create_index(op.f('ix_in_app_notifications_user_id'), 'in_app_notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_in_app_notifications_document_id'), 'in_app_notifications', ['document_id'], unique=False)
    op.create_index(op.f('ix_in_app_notifications_reminder_type'), 'in_app_notifications', ['reminder_type'], unique=False)
    op.create_index(op.f('ix_in_app_notifications_is_del'), 'in_app_notifications', ['is_del'], unique=False)
    op.create_index(op.f('ix_in_app_notifications_created_at'), 'in_app_notifications', ['created_at'], unique=False)
    op.create_index(op.f('ix_in_app_notifications_updated_at'), 'in_app_notifications', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop in_app_notifications table and its indexes
    op.drop_index(op.f('ix_in_app_notifications_updated_at'), table_name='in_app_notifications')
    op.drop_index(op.f('ix_in_app_notifications_created_at'), table_name='in_app_notifications')
    op.drop_index(op.f('ix_in_app_notifications_is_del'), table_name='in_app_notifications')
    op.drop_index(op.f('ix_in_app_notifications_reminder_type'), table_name='in_app_notifications')
    op.drop_index(op.f('ix_in_app_notifications_document_id'), table_name='in_app_notifications')
    op.drop_index(op.f('ix_in_app_notifications_user_id'), table_name='in_app_notifications')
    op.drop_index(op.f('ix_in_app_notifications_id'), table_name='in_app_notifications')
    op.drop_table('in_app_notifications')
    
    # Drop reminder_schedules table and its indexes
    op.drop_index('uq_reminder_schedules_document_user_type_pending', table_name='reminder_schedules')
    op.drop_index(op.f('ix_reminder_schedules_updated_at'), table_name='reminder_schedules')
    op.drop_index(op.f('ix_reminder_schedules_created_at'), table_name='reminder_schedules')
    op.drop_index(op.f('ix_reminder_schedules_status'), table_name='reminder_schedules')
    op.drop_index(op.f('ix_reminder_schedules_send_at'), table_name='reminder_schedules')
    op.drop_index(op.f('ix_reminder_schedules_reminder_type'), table_name='reminder_schedules')
    op.drop_index(op.f('ix_reminder_schedules_user_id'), table_name='reminder_schedules')
    op.drop_index(op.f('ix_reminder_schedules_document_id'), table_name='reminder_schedules')
    op.drop_index(op.f('ix_reminder_schedules_id'), table_name='reminder_schedules')
    op.drop_table('reminder_schedules')

