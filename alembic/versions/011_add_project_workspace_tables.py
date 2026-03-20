"""add project workspace tables (notes, conversations, map_state, upload project_id)

Revision ID: 011
Revises: 010
Create Date: 2026-03-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. project_notes
    op.create_table(
        'project_notes',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 2. project_conversations
    op.create_table(
        'project_conversations',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False, server_default='New conversation'),
        sa.Column('messages', JSON(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 3. Add map_state JSON column to projects
    op.add_column('projects', sa.Column('map_state', JSON(), nullable=True))

    # 4. Add project_id to uploaded_documents
    op.add_column('uploaded_documents', sa.Column('project_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_uploaded_documents_project_id',
        'uploaded_documents', 'projects',
        ['project_id'], ['id'],
    )
    op.create_index('ix_uploaded_documents_project_id', 'uploaded_documents', ['project_id'])


def downgrade() -> None:
    op.drop_index('ix_uploaded_documents_project_id', table_name='uploaded_documents')
    op.drop_constraint('fk_uploaded_documents_project_id', 'uploaded_documents', type_='foreignkey')
    op.drop_column('uploaded_documents', 'project_id')
    op.drop_column('projects', 'map_state')
    op.drop_table('project_conversations')
    op.drop_table('project_notes')
