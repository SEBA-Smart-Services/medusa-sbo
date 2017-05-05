from app import db

# trend log values, stored in report server
class Alarm(db.Model):
    """
    Represents the StruxureWareReportsDB.tb.AlarmsEvents table
    (StruxureWare alarms)

    """

    __tablename__ = 'tbAlarmsEvents'

    id = db.Column('SeqNo', db.BigInteger, primary_key=True)
    alarm_id = db.Column('UniqueAlarmId', db.String(50))
    datetimestamp = db.Column('TriggeredTimestamp', db.DateTime)
    point = db.Column('MonitoredPoint', db.String(1024))
    state = db.Column('AlarmState', db.Integer)
    description = db.Column('AlarmText', db.String(1024))
    category = db.Column('Category', db.String(128))
    count = db.Column('Count', db.Integer)
