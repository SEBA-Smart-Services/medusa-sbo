from flask import render_template, redirect, url_for
from app import app, db
from app.models import Alarm, Site

@app.route('/site/<sitename>/alarms')
def alarm_list(sitename):
    return redirect(url_for('alarm_list_paged', sitename=sitename, page_number=1))

# alarms list page
@app.route('/site/<sitename>/alarms/<int:page_number>', methods=['GET'])
def alarm_list_paged(sitename, page_number):

    ALARMS_PER_PAGE = 20
    # page_number = 1

    def transform_alarm_data(alarm_list):
        alarm_resp  = []
        for alarm in alarm_list:
            alarm_dict = {}
            alarm_dict["timestamp"] = alarm.TriggeredTimestamp
            alarm_dict["priority"] = alarm.Priority
            alarm_dict["description"] = alarm.AlarmText
            alarm_dict["state"] = alarm.alarm_state_text()
            alarm_resp.append(alarm_dict)
        return alarm_resp

    if sitename == "all":
        site = None
        alarms = Alarm.query.order_by(
            Alarm.TriggeredTimestamp.desc()
        ).paginate(
           page_number,
           ALARMS_PER_PAGE,
           False
        ).items

    else:
        site = Site.query.filter_by(name=sitename).one()
        alarms = Alarm.query.filter_by(
            site_id=site.id
        ).order_by(
            Alarm.TriggeredTimestamp.desc()
        ).paginate(
            page_number,
            ALARMS_PER_PAGE,
            False
        ).items

    alarm_resp = transform_alarm_data(alarms)

    return render_template(
        'alarms.html',
        site=site,
        alarms=alarm_resp,
        page_number=page_number
    )
