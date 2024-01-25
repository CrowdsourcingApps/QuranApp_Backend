"""added ayah part text

Revision ID: 6ba0c5986f62
Revises: 25779d22b738
Create Date: 2024-01-22 23:16:25.291990

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ba0c5986f62'
down_revision: Union[str, None] = '25779d22b738'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ayah_part_texts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('text', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ayah_part_texts')
    # ### end Alembic commands ###