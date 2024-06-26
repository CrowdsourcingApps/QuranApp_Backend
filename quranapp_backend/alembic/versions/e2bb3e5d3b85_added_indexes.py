"""added indexes

Revision ID: e2bb3e5d3b85
Revises: abb6650a4426
Create Date: 2024-03-31 17:27:41.123186

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2bb3e5d3b85'
down_revision: Union[str, None] = 'abb6650a4426'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_ayahs_ayah_in_surah_number', 'ayahs', ['ayah_in_surah_number'], unique=False)
    op.create_index('ix_ayahs_surah_number', 'ayahs', ['surah_number'], unique=False)
    op.create_index('ix_mushaf_pages_mushaf_id', 'mushaf_pages', ['mushaf_id'], unique=False)
    op.create_index('ix_reciters_name_riwayah', 'reciters', ['name', 'riwayah'], unique=True)
    op.create_index('ix_recordings_user_id_is_deleted', 'recordings', ['user_id', 'is_deleted'], unique=False)
    op.create_index('ix_shared_recordings_recipient_id', 'shared_recordings', ['recipient_id'], unique=False)
    op.create_index('ix_shared_recordings_recording_id', 'shared_recordings', ['recording_id'], unique=False)
    op.create_index('ix_users_alias', 'users', ['alias'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_users_alias', table_name='users')
    op.drop_index('ix_shared_recordings_recording_id', table_name='shared_recordings')
    op.drop_index('ix_shared_recordings_recipient_id', table_name='shared_recordings')
    op.drop_index('ix_recordings_user_id_is_deleted', table_name='recordings')
    op.drop_index('ix_reciters_name_riwayah', table_name='reciters')
    op.drop_index('ix_mushaf_pages_mushaf_id', table_name='mushaf_pages')
    op.drop_index('ix_ayahs_surah_number', table_name='ayahs')
    op.drop_index('ix_ayahs_ayah_in_surah_number', table_name='ayahs')
    # ### end Alembic commands ###
