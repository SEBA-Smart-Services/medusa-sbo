"""empty message

Revision ID: a3665d5105f1
Revises: 375aee4d1f5d
Create Date: 2017-05-14 14:11:23.172695

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a3665d5105f1'
down_revision = '375aee4d1f5d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('alarm',
    sa.Column('SeqNo', sa.BigInteger(), nullable=False),
    sa.Column('MonitoredPoInteger', sa.String(length=1024), nullable=True),
    sa.Column('PreviousAlarmState', sa.Integer(), nullable=True),
    sa.Column('AlarmState', sa.Integer(), nullable=True),
    sa.Column('TriggeredTimestamp', sa.DateTime(), nullable=True),
    sa.Column('AdvancedEvaluationState', sa.Integer(), nullable=True),
    sa.Column('AlarmType', sa.String(length=1024), nullable=True),
    sa.Column('MonitoredValue', sa.String(length=50), nullable=True),
    sa.Column('DomainName', sa.String(length=1024), nullable=True),
    sa.Column('AcknowledgedBy', sa.String(length=80), nullable=True),
    sa.Column('Priority', sa.Integer(), nullable=True),
    sa.Column('Count', sa.Integer(), nullable=True),
    sa.Column('AcknowledgeTime', sa.DateTime(), nullable=True),
    sa.Column('BasicEvaluationState', sa.Boolean(), nullable=True),
    sa.Column('Logging', sa.Boolean(), nullable=True),
    sa.Column('Hidden', sa.Boolean(), nullable=True),
    sa.Column('Category', sa.String(length=128), nullable=True),
    sa.Column('AssignedTo', sa.String(length=80), nullable=True),
    sa.Column('AssignState', sa.Integer(), nullable=True),
    sa.Column('DisabledBy', sa.Integer(), nullable=True),
    sa.Column('AlarmStateSeqNo', sa.BigInteger(), nullable=True),
    sa.Column('CheckedSteps', sa.String(length=512), nullable=True),
    sa.Column('AudibleAlert', sa.Boolean(), nullable=True),
    sa.Column('FlashingAlert', sa.Boolean(), nullable=True),
    sa.Column('Silence', sa.Boolean(), nullable=True),
    sa.Column('PendingState', sa.Integer(), nullable=True),
    sa.Column('PendingCommand', sa.Integer(), nullable=True),
    sa.Column('ServerOffline', sa.Boolean(), nullable=True),
    sa.Column('SystemEventId', sa.BigInteger(), nullable=True),
    sa.Column('Module', sa.Integer(), nullable=True),
    sa.Column('HasAttachment', sa.Boolean(), nullable=True),
    sa.Column('UniqueAlarmId', sa.String(length=50), nullable=True),
    sa.Column('SystemAlarmId', sa.Integer(), nullable=True),
    sa.Column('AlarmText', sa.String(length=1024), nullable=True),
    sa.Column('Command', sa.String(length=128), nullable=True),
    sa.Column('OriginatedGUID', sa.String(length=50), nullable=True),
    sa.Column('DateTimeStamp', sa.DateTime(), nullable=True),
    sa.Column('site_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['site_id'], ['site.ID'], ),
    sa.PrimaryKeyConstraint('SeqNo')
    )
    op.add_column('tbAlarmsEvents', sa.Column('AcknowledgeTime', sa.DateTime(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('AcknowledgedBy', sa.String(length=80), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('AdvancedEvaluationState', sa.Integer(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('AlarmStateSeqNo', sa.BigInteger(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('AlarmType', sa.String(length=1024), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('AssignState', sa.Integer(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('AssignedTo', sa.String(length=80), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('AudibleAlert', sa.Boolean(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('BasicEvaluationState', sa.Boolean(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('CheckedSteps', sa.String(length=512), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('Command', sa.String(length=128), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('DateTimeStamp', sa.DateTime(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('DisabledBy', sa.Integer(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('DomainName', sa.String(length=1024), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('FlashingAlert', sa.Boolean(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('HasAttachment', sa.Boolean(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('Hidden', sa.Boolean(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('Logging', sa.Boolean(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('Module', sa.Integer(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('MonitoredPoInteger', sa.String(length=1024), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('MonitoredValue', sa.String(length=50), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('OriginatedGUID', sa.String(length=50), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('PendingCommand', sa.Integer(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('PendingState', sa.Integer(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('PreviousAlarmState', sa.Integer(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('Priority', sa.Integer(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('ServerOffline', sa.Boolean(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('Silence', sa.Boolean(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('SystemAlarmId', sa.Integer(), nullable=True))
    op.add_column('tbAlarmsEvents', sa.Column('SystemEventId', sa.BigInteger(), nullable=True))
    op.drop_column('tbAlarmsEvents', 'MonitoredPoint')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tbAlarmsEvents', sa.Column('MonitoredPoint', mysql.VARCHAR(length=1024), nullable=True))
    op.drop_column('tbAlarmsEvents', 'SystemEventId')
    op.drop_column('tbAlarmsEvents', 'SystemAlarmId')
    op.drop_column('tbAlarmsEvents', 'Silence')
    op.drop_column('tbAlarmsEvents', 'ServerOffline')
    op.drop_column('tbAlarmsEvents', 'Priority')
    op.drop_column('tbAlarmsEvents', 'PreviousAlarmState')
    op.drop_column('tbAlarmsEvents', 'PendingState')
    op.drop_column('tbAlarmsEvents', 'PendingCommand')
    op.drop_column('tbAlarmsEvents', 'OriginatedGUID')
    op.drop_column('tbAlarmsEvents', 'MonitoredValue')
    op.drop_column('tbAlarmsEvents', 'MonitoredPoInteger')
    op.drop_column('tbAlarmsEvents', 'Module')
    op.drop_column('tbAlarmsEvents', 'Logging')
    op.drop_column('tbAlarmsEvents', 'Hidden')
    op.drop_column('tbAlarmsEvents', 'HasAttachment')
    op.drop_column('tbAlarmsEvents', 'FlashingAlert')
    op.drop_column('tbAlarmsEvents', 'DomainName')
    op.drop_column('tbAlarmsEvents', 'DisabledBy')
    op.drop_column('tbAlarmsEvents', 'DateTimeStamp')
    op.drop_column('tbAlarmsEvents', 'Command')
    op.drop_column('tbAlarmsEvents', 'CheckedSteps')
    op.drop_column('tbAlarmsEvents', 'BasicEvaluationState')
    op.drop_column('tbAlarmsEvents', 'AudibleAlert')
    op.drop_column('tbAlarmsEvents', 'AssignedTo')
    op.drop_column('tbAlarmsEvents', 'AssignState')
    op.drop_column('tbAlarmsEvents', 'AlarmType')
    op.drop_column('tbAlarmsEvents', 'AlarmStateSeqNo')
    op.drop_column('tbAlarmsEvents', 'AdvancedEvaluationState')
    op.drop_column('tbAlarmsEvents', 'AcknowledgedBy')
    op.drop_column('tbAlarmsEvents', 'AcknowledgeTime')
    op.drop_table('alarm')
    # ### end Alembic commands ###
