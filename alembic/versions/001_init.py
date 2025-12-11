from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('registration_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('is_disabled', sa.Boolean, default=False),
        sa.Column('force_password_change', sa.Boolean, default=False)
    )

    op.create_table(
        'jwt_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('token', sa.Text, nullable=False),
        sa.Column('user_id', postgresql.UUID, sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('created', sa.DateTime(timezone=True)),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=False),
        sa.Column('device_name', sa.String(100), nullable=False),
        sa.Column('on_creation_ip', sa.String(45), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean, default=False)
    )

    op.create_table(
        'translations',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('translation_code', sa.String(2), nullable=False, unique=True, index=True),
        sa.Column('full_name', sa.String(100), nullable=False)
    )

    op.create_table(
        'topic',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('name_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('creator_user_id', postgresql.UUID, sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('imported', sa.Boolean, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('edited_at', sa.DateTime(timezone=True))
    )

    op.create_table(
        'media_object',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('uploaded_by_user_id', postgresql.UUID, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False),
        sa.Column('used_topic_id', sa.Integer, nullable=True),  # FK добавим позже
        sa.Column('used_user_id', postgresql.UUID, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('obj_type', sa.String(20), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('sha256_hash_original', sa.String(64), nullable=False, unique=True),
        sa.Column('sha256_hash_thumb', sa.String(64), nullable=False, unique=True),
        sa.Column('sha256_hash_small', sa.String(64), nullable=True, unique=True),
        sa.Column('sha256_hash_medium', sa.String(64), nullable=True, unique=True),
        sa.Column('sha256_hash_large', sa.String(64), nullable=True, unique=True),
        sa.Column('has_small', sa.Boolean, default=False),
        sa.Column('has_medium', sa.Boolean, default=False),
        sa.Column('has_large', sa.Boolean, default=False)
    )

    op.create_table(
        'categories',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text),
        sa.Column('display_mode', sa.String(20), nullable=False)
    )

    op.create_table(
        'categories_in_topic',
        sa.Column('topic_id', sa.Integer, sa.ForeignKey('topic.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('category_id', sa.Integer, sa.ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)
    )

    op.create_table(
        'tags',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text)
    )

    op.create_table(
        'tags_in_topic',
        sa.Column('topic_id', sa.Integer, sa.ForeignKey('topic.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', sa.Integer, sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
    )

    op.create_table(
        'topic_links',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('topic_id', sa.Integer, sa.ForeignKey('topic.id', ondelete='CASCADE'), nullable=False),
        sa.Column('link_name', sa.String(200), nullable=False),
        sa.Column('link_url', sa.String(500), nullable=False),
        sa.Column('away', sa.Boolean, default=False)
    )

    op.create_table(
        'topic_translations',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('translation_id', sa.Integer, sa.ForeignKey('translations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_id', sa.Integer, sa.ForeignKey('topic.id', ondelete='CASCADE'), nullable=False),
        sa.Column('creator_user_id', postgresql.UUID, sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('parse_mode', sa.String(20), nullable=False),
        sa.Column('last_edited_by', postgresql.UUID, sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('first', sa.Boolean, nullable=False)
    )

    op.create_table(
        'audit',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('action_type', sa.String(20), nullable=False),
        sa.Column('user_id', postgresql.UUID, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.Text)
    )

    op.create_table(
        'audit_effected_objects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('audit_id', postgresql.UUID, sa.ForeignKey('audit.id', ondelete='CASCADE'), nullable=False),
        sa.Column('object_type', sa.String(20), nullable=False),
        sa.Column('object_id', sa.Integer, nullable=False)
    )

    op.create_table(
        'application_parameters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.Text, nullable=False, unique=True, index=True),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('visibility', sa.String(20), nullable=False),
        sa.Column('default_value', sa.Text)
    )

    op.create_table(
        'ap_value',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('value', sa.Text),
        sa.Column('override', sa.Boolean, default=False),
        sa.Column('ap_id', postgresql.UUID, sa.ForeignKey('application_parameters.id', ondelete='CASCADE'), nullable=False)
    )

def downgrade():
    op.drop_table('ap_value')
    op.drop_table('application_parameters')
    op.drop_table('audit_effected_objects')
    op.drop_table('audit')
    op.drop_table('topic_translations')
    op.drop_table('topic_links')
    op.drop_table('tags_in_topic')
    op.drop_table('tags')
    op.drop_table('categories_in_topic')
    op.drop_table('categories')
    op.drop_table('media_object')
    op.drop_table('topic')
    op.drop_table('translations')
    op.drop_table('jwt_tokens')
    op.drop_table('users')
