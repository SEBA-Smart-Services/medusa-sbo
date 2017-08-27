from app import db, app

# alarm, stored in report server
class WebReportsAlarm(db.Model):
    """
    Represents the StruxureWareReportsDB.tb.AlarmsEvents table
    (StruxureWare alarms)

    SeqNo,MonitoredPoint,PreviousAlarmState,AlarmState,TriggeredTimestamp,
    AdvancedEvaluationState,AlarmType,MonitoredValue,DomainName,AcknowledgedBy,
    Priority,Count,AcknowledgeTime,BasicEvaluationState,Logging,Hidden,
    Category,AssignedTo,AssignState,DisabledBy,AlarmStateSeqNo,CheckedSteps,
    AudibleAlert,FlashingAlert,Silence,PendingState,PendingCommand,
    ServerOffline,SystemEventId,Module,HasAttachment,UniqueAlarmId,
    SystemAlarmId,AlarmText,Command,OriginatedGUID,DateTimeStamp

    """

    __tablename__ = 'tbAlarmsEvents'

    id = db.Column('SeqNo', db.BigInteger, primary_key=True)
    MonitoredPoint = db.Column('MonitoredPoint', db.String(1024))
    PreviousAlarmState = db.Column('PreviousAlarmState', db.Integer)
    AlarmState = db.Column('AlarmState', db.Integer)
    TriggeredTimestamp = db.Column('TriggeredTimestamp', db.DateTime)
    AdvancedEvaluationState = db.Column('AdvancedEvaluationState', db.Integer)
    AlarmType = db.Column('AlarmType', db.String(1024))
    MonitoredValue = db.Column('MonitoredValue', db.String(50))
    DomainName = db.Column('DomainName', db.String(1024))
    AcknowledgedBy = db.Column('AcknowledgedBy', db.String(80))
    Priority = db.Column('Priority', db.Integer)
    Count = db.Column('Count', db.Integer)
    AcknowledgeTime = db.Column('AcknowledgeTime', db.DateTime)
    BasicEvaluationState = db.Column('BasicEvaluationState', db.Boolean)
    Logging = db.Column('Logging', db.Boolean)
    Hidden = db.Column('Hidden', db.Boolean)
    Category = db.Column('Category', db.String(128))
    AssignedTo = db.Column('AssignedTo', db.String(80))
    AssignState = db.Column('AssignState', db.Integer)
    DisabledBy = db.Column('DisabledBy', db.Integer)
    AlarmStateSeqNo = db.Column('AlarmStateSeqNo', db.BigInteger)
    CheckedSteps = db.Column('CheckedSteps', db.String(512))
    AudibleAlert = db.Column('AudibleAlert', db.Boolean)
    FlashingAlert = db.Column('FlashingAlert', db.Boolean)
    Silence = db.Column('Silence', db.Boolean)
    PendingState = db.Column('PendingState', db.Integer)
    PendingCommand = db.Column('PendingCommand', db.Integer)
    ServerOffline = db.Column('ServerOffline', db.Boolean)
    SystemEventId = db.Column('SystemEventId', db.BigInteger)
    Module = db.Column('Module', db.Integer)
    HasAttachment = db.Column('HasAttachment', db.Boolean)
    UniqueAlarmId = db.Column('UniqueAlarmId', db.String(50))
    SystemAlarmId = db.Column('SystemAlarmId', db.Integer)
    AlarmText = db.Column('AlarmText', db.String(1024))
    Command = db.Column('Command', db.String(128))
    OriginatedGUID = db.Column('OriginatedGUID', db.String(50))
    DateTimeStamp = db.Column('DateTimeStamp', db.DateTime)


# TODO:
# inherit from tbAlarmsEvents
# got a weird error first go:
# File "/var/www/medusa/env/lib/python3.5/site-packages/sqlalchemy/sql/selectable.py", line 979, in _join_condition
#     (a.description, b.description, hint))
# sqlalchemy.exc.NoForeignKeysError: Can't find any foreign key relationships between 'tbAlarmsEvents' and 'alarm'.
# class Alarm(WebReportsAlarm):
class Alarm(db.Model):
    """
    A replication of site StruxureWareReportsDB.tb.AlarmsEvents table in medusa db
    with site_id and medusa_id

    """

    medusa_id = db.Column('Medusa_ID', db.Integer, primary_key=True)
    site_id = db.Column('site_id', db.Integer, db.ForeignKey('site.ID'), nullable=False)
    id = db.Column('SeqNo', db.BigInteger)
    MonitoredPoint = db.Column('MonitoredPoint', db.String(1024))
    PreviousAlarmState = db.Column('PreviousAlarmState', db.Integer)
    AlarmState = db.Column('AlarmState', db.Integer)
    TriggeredTimestamp = db.Column('TriggeredTimestamp', db.DateTime)
    AdvancedEvaluationState = db.Column('AdvancedEvaluationState', db.Integer)
    AlarmType = db.Column('AlarmType', db.String(1024))
    MonitoredValue = db.Column('MonitoredValue', db.String(50))
    DomainName = db.Column('DomainName', db.String(1024))
    AcknowledgedBy = db.Column('AcknowledgedBy', db.String(80))
    Priority = db.Column('Priority', db.Integer)
    Count = db.Column('Count', db.Integer)
    AcknowledgeTime = db.Column('AcknowledgeTime', db.DateTime)
    BasicEvaluationState = db.Column('BasicEvaluationState', db.Boolean)
    Logging = db.Column('Logging', db.Boolean)
    Hidden = db.Column('Hidden', db.Boolean)
    Category = db.Column('Category', db.String(128))
    AssignedTo = db.Column('AssignedTo', db.String(80))
    AssignState = db.Column('AssignState', db.Integer)
    DisabledBy = db.Column('DisabledBy', db.Integer)
    AlarmStateSeqNo = db.Column('AlarmStateSeqNo', db.BigInteger)
    CheckedSteps = db.Column('CheckedSteps', db.String(512))
    AudibleAlert = db.Column('AudibleAlert', db.Boolean)
    FlashingAlert = db.Column('FlashingAlert', db.Boolean)
    Silence = db.Column('Silence', db.Boolean)
    PendingState = db.Column('PendingState', db.Integer)
    PendingCommand = db.Column('PendingCommand', db.Integer)
    ServerOffline = db.Column('ServerOffline', db.Boolean)
    SystemEventId = db.Column('SystemEventId', db.BigInteger)
    Module = db.Column('Module', db.Integer)
    HasAttachment = db.Column('HasAttachment', db.Boolean)
    UniqueAlarmId = db.Column('UniqueAlarmId', db.String(50))
    SystemAlarmId = db.Column('SystemAlarmId', db.Integer)
    AlarmText = db.Column('AlarmText', db.String(1024))
    Command = db.Column('Command', db.String(128))
    OriginatedGUID = db.Column('OriginatedGUID', db.String(50))
    DateTimeStamp = db.Column('DateTimeStamp', db.DateTime)

    def alarm_state_text(self):
        """
        return a human-friendly representation of the AlarmState field
        """
        alarm_state_text_dict = {
            0: 'Normal',
            1: 'Alarm',
            2: 'Checked',
            3: 'Reset',
            4: 'Disabled'
        }
        return alarm_state_text_dict[self.AlarmState]


class LogTimeValue(db.Model):
    """
    A replication of site StruxureWareReportsDB.tbLogTimeValues table in medusa db
    with site_id and medusa_id

    """
    # __tablename__ = 'tbLogTimeValues'     obsolete since migrating away from webreports
    medusa_id = db.Column('Medusa_ID', db.Integer, primary_key=True)
    site_id = db.Column('site_id', db.Integer, db.ForeignKey('site.ID'), nullable=False)
    datetimestamp = db.Column('DateTimeStamp', db.DateTime)
    seqno = db.Column('SeqNo', db.BigInteger)
    float_value = db.Column('FloatVALUE', db.Float)
    parent_id = db.Column('ParentID', db.Integer)
    odometer_value = db.Column('OdometerValue', db.Float)

# trend logs, as they exist in the struxureware object heirarchy
class LoggedEntity(db.Model):
    """
    A replication of site StruxureWareReportsDB.tbLoggedEntities table in medusa db
    with site_id and medusa_id

    """
    # __tablename__ = 'tbLoggedEntities'     obsolete since migrating away from webreports
    medusa_id = db.Column('Medusa_ID', db.Integer, primary_key=True)
    site_id = db.Column('site_id', db.Integer, db.ForeignKey('site.ID'), nullable=False)
    id = db.Column('ID', db.Integer)
    guid = db.Column('GUID', db.String(50))
    path = db.Column('Path', db.String(1024))
    descr = db.Column('Descr', db.String(512))
    disabled = db.Column('Disabled', db.Boolean)
    last_mod = db.Column('LastMod', db.DateTime)
    version = db.Column('Version', db.Integer)
    type = db.Column('Type', db.String(80))
    log_point = db.Column('LogPoint', db.String(1024))
    unit_prefix = db.Column('UNITPREFIX', db.String(512))
    unit = db.Column('Unit', db.String(512))
    base_value = db.Column('BaseValue', db.Float)
    meter_startpoint = db.Column('MeterStartPoint', db.Float)
    last_read_value = db.Column('LastReadValue', db.Float)
