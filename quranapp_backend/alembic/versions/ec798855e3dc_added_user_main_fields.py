"""Added User main fields

Revision ID: ec798855e3dc
Revises: 0181db885bcd
Create Date: 2023-10-18 18:33:55.822146

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec798855e3dc'
down_revision: Union[str, None] = '0181db885bcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('alias', sa.String(), nullable=False))
    op.add_column('users', sa.Column('name', sa.String(), nullable=False))
    op.add_column('users', sa.Column('surname', sa.String(), nullable=False))
    op.create_unique_constraint("alias_unique_constraint", 'users', ['alias'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("alias_unique_constraint", 'users', type_='unique')
    op.drop_column('users', 'surname')
    op.drop_column('users', 'name')
    op.drop_column('users', 'alias')
    # ### end Alembic commands ###
