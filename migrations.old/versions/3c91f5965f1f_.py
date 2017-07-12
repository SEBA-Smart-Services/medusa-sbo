"""empty message

Revision ID: 3c91f5965f1f
Revises: 7082a469fba9
Create Date: 2017-04-27 07:12:09.052059

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c91f5965f1f'
down_revision = '7082a469fba9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('functional_descriptor',
    sa.Column('ID', sa.Integer(), nullable=False),
    sa.Column('Name', sa.String(length=512), nullable=True),
    sa.Column('Type_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['Type_id'], ['asset_type.ID'], ),
    sa.PrimaryKeyConstraint('ID')
    )
    op.create_table('inbuildings_config',
    sa.Column('ID', sa.Integer(), nullable=False),
    sa.Column('Site_id', sa.Integer(), nullable=True),
    sa.Column('Enabled', sa.Boolean(), nullable=True),
    sa.Column('Connection_key', sa.String(length=512), nullable=True),
    sa.ForeignKeyConstraint(['Site_id'], ['site.ID'], ),
    sa.PrimaryKeyConstraint('ID')
    )
    op.create_table('issue_history',
    sa.Column('ID', sa.Integer(), nullable=False),
    sa.Column('Issues', sa.Integer(), nullable=True),
    sa.Column('Timestamp_id', sa.Integer(), nullable=True),
    sa.Column('Site_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['Site_id'], ['site.ID'], ),
    sa.ForeignKeyConstraint(['Timestamp_id'], ['issue_history_timestamp.ID'], ),
    sa.PrimaryKeyConstraint('ID')
    )
    op.create_table('algo_asset_mapping',
    sa.Column('Asset_id', sa.Integer(), nullable=False),
    sa.Column('Algorithm_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['Algorithm_id'], ['algorithm.ID'], ),
    sa.ForeignKeyConstraint(['Asset_id'], ['asset.ID'], ),
    sa.PrimaryKeyConstraint('Asset_id', 'Algorithm_id')
    )
    op.create_table('algo_exclusions',
    sa.Column('Asset_id', sa.Integer(), nullable=False),
    sa.Column('Algorithm_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['Algorithm_id'], ['algorithm.ID'], ),
    sa.ForeignKeyConstraint(['Asset_id'], ['asset.ID'], ),
    sa.PrimaryKeyConstraint('Asset_id', 'Algorithm_id')
    )
    op.create_table('algo_function_mapping',
    sa.Column('Algorithm_id', sa.Integer(), nullable=False),
    sa.Column('FunctionalDescriptor_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['Algorithm_id'], ['algorithm.ID'], ),
    sa.ForeignKeyConstraint(['FunctionalDescriptor_id'], ['functional_descriptor.ID'], ),
    sa.PrimaryKeyConstraint('Algorithm_id', 'FunctionalDescriptor_id')
    )
    op.create_table('asset_function_mapping',
    sa.Column('Asset_id', sa.Integer(), nullable=False),
    sa.Column('FunctionalDescriptor_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['Asset_id'], ['asset.ID'], ),
    sa.ForeignKeyConstraint(['FunctionalDescriptor_id'], ['functional_descriptor.ID'], ),
    sa.PrimaryKeyConstraint('Asset_id', 'FunctionalDescriptor_id')
    )
    op.create_table('asset_point',
    sa.Column('ID', sa.Integer(), nullable=False),
    sa.Column('Name', sa.String(length=512), nullable=True),
    sa.Column('Asset_id', sa.Integer(), nullable=True),
    sa.Column('PointType_id', sa.Integer(), nullable=True),
    sa.Column('LoggedEntity_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['Asset_id'], ['asset.ID'], ),
    sa.ForeignKeyConstraint(['PointType_id'], ['point_type.ID'], ),
    sa.PrimaryKeyConstraint('ID')
    )
    op.create_table('inbuildings_asset',
    sa.Column('ID', sa.Integer(), nullable=False),
    sa.Column('Name', sa.String(length=512), nullable=True),
    sa.Column('Location', sa.String(length=512), nullable=True),
    sa.Column('Group', sa.String(length=512), nullable=True),
    sa.Column('Site_id', sa.Integer(), nullable=True),
    sa.Column('Asset_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['Asset_id'], ['asset.ID'], ),
    sa.ForeignKeyConstraint(['Site_id'], ['site.ID'], ),
    sa.PrimaryKeyConstraint('ID')
    )
    op.create_table('result',
    sa.Column('ID', sa.Integer(), nullable=False),
    sa.Column('First_timestamp', sa.DateTime(), nullable=True),
    sa.Column('Recent_timestamp', sa.DateTime(), nullable=True),
    sa.Column('Asset_id', sa.Integer(), nullable=True),
    sa.Column('Algorithm_id', sa.Integer(), nullable=True),
    sa.Column('Result', sa.Float(), nullable=True),
    sa.Column('Passed', sa.Boolean(), nullable=True),
    sa.Column('Active', sa.Boolean(), nullable=True),
    sa.Column('Acknowledged', sa.Boolean(), nullable=True),
    sa.Column('Occurances', sa.Integer(), nullable=True),
    sa.Column('Recent', sa.Boolean(), nullable=True),
    sa.Column('Notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['Algorithm_id'], ['algorithm.ID'], ),
    sa.ForeignKeyConstraint(['Asset_id'], ['asset.ID'], ),
    sa.PrimaryKeyConstraint('ID')
    )
    op.create_table('points_checked',
    sa.Column('Result_id', sa.Integer(), nullable=False),
    sa.Column('Point_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['Point_id'], ['asset_point.ID'], ),
    sa.ForeignKeyConstraint(['Result_id'], ['result.ID'], ),
    sa.PrimaryKeyConstraint('Result_id', 'Point_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('points_checked')
    op.drop_table('result')
    op.drop_table('inbuildings_asset')
    op.drop_table('asset_point')
    op.drop_table('asset_function_mapping')
    op.drop_table('algo_function_mapping')
    op.drop_table('algo_exclusions')
    op.drop_table('algo_asset_mapping')
    op.drop_table('issue_history')
    op.drop_table('inbuildings_config')
    op.drop_table('functional_descriptor')
    # ### end Alembic commands ###