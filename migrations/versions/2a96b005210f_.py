"""empty message

Revision ID: 2a96b005210f
Revises: 8d359f1a6b4b
Create Date: 2017-09-20 08:34:45.376371

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a96b005210f'
down_revision = '8d359f1a6b4b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('deliverable', sa.Column('description', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('deliverable', 'description')
    # ### end Alembic commands ###
