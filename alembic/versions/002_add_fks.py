from alembic import op
import sqlalchemy as sa


revision = '002_add_fks'
down_revision = '001_init'
branch_labels = None
depends_on = None


def upgrade():
    op.create_foreign_key(
        'fk_media_object_used_topic',
        'media_object', 'topic',
        ['used_topic_id'], ['id'],
        ondelete='SET NULL'
    )

    op.add_column('topic', sa.Column('cover_image_id', sa.Integer, nullable=True))
    op.create_foreign_key(
        'fk_topic_cover_image',
        'topic', 'media_object',
        ['cover_image_id'], ['id'],
        ondelete='SET NULL'
    )

def downgrade():
    op.drop_constraint('fk_topic_cover_image', 'topic', type_='foreignkey')
    op.drop_column('topic', 'cover_image_id')
    op.drop_constraint('fk_media_object_used_topic', 'media_object', type_='foreignkey')
