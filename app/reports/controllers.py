from app import app, event
from app.models import Site, Asset, Result
from app.models.ITP import Project, ITP, Deliverable, Deliverable_ITC_map, Deliverable_check_map, Deliverable_type, ITC_group
from app.ticket.models import FlicketTicket
from flask import render_template, url_for, redirect
from flask_weasyprint import HTML, CSS, render_pdf
import datetime

# provide a url to download a report for a site
@app.route('/site/<sitename>/report')
def report_page(sitename):
    site = Site.query.filter_by(name=sitename).one()
    html = generate_report_html(site)
    return render_pdf(html)

# provide a url to download a report for an ITP
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/report')
def ITP_report_page(siteid, projectid, ITPid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid).first()
    project_ITP = ITP.query.filter_by(id=ITPid).first()
    deliverables = Deliverable.query.filter_by(ITP_id=project_ITP.id).all()
    deliverable_types = Deliverable_type.query.filter(Deliverable_type.id.in_([deliverable.deliverable_type_id for deliverable in deliverables])).all()
    today = datetime.datetime.now()
    # image = flask_weasyprint.default_url_fetcher("/static/img/logo-schneider-electric.png")
    ITC_groups = ITC_group.query.all()
    ITC_groups = sorted(ITC_groups, key=lambda x: x.name)

    DDC_group = ['Automation Server', 'AS-P', 'AS']
    #
    # print(deliverable_types)
    # for deliverable_type in deliverable_types:
    #     for ITC in deliverable_type.ITC:
    #         print(ITC)
    #         print(ITC.deliverable_ITC_map.filter_by())
    #         print(ITC.deliverable_ITC_map.major_revision_number)
    #
    # for deliverable in deliverables:
    #     print(deliverable)
    #     if deliverable.type.name in DDC_group:
    #         print(deliverable.type)

    ITCs = []
    for deliverable in deliverables:
        ITCs += Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable.id).all()

    ITCs = sorted(ITCs, key=lambda x: x.ITC.group.name)
    # print(ITCs)
    # for ITC in ITCs:
    #     print(ITC.ITC.ITC_group_id)
    # print(Deliverable_ITC_map.query.filter(Deliverable_ITC_map.ITC_id.in_([ITC_group.deliverable.id for ITC_group in ITC_groups])).all())

    html = render_template('ITP_report.html',
                            site=site,
                            project=project,
                            project_ITP=project_ITP,
                            deliverables=deliverables,
                            ITCs=ITCs,
                            deliverable_types=deliverable_types,
                            today=today,
                            groups=ITC_groups,
                            DDC_group=DDC_group)
    return render_pdf(HTML(string=html))

# provide a url to download a report for all delvierables in an ITP
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/report')
def deliverables_report_page(siteid, projectid, ITPid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid).first()
    project_ITP = ITP.query.filter_by(id=ITPid).first()
    deliverables = Deliverable.query.filter_by(ITP_id=project_ITP.id).all()

    html = render_template('deliverable_report.html', site=site, project=project, project_ITP=project_ITP, deliverables=deliverables)
    return render_pdf(HTML(string=html))

# provide a url to download a report for an ITC
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/<deliverableid>/ITC/<ITCid>/checks/report')
def checks_report_page(siteid, projectid, ITPid, deliverableid, ITCid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid).first()
    project_ITP = ITP.query.filter_by(id=ITPid).first()
    deliverable = Deliverable.query.filter_by(ITP_id=project_ITP.id).first()
    ITP_ITC = Deliverable_ITC_map.query.filter_by(id=ITCid).first()
    checks = Deliverable_check_map.query.filter_by(deliverable_ITC_map_id=ITP_ITC.id).all()

    html = render_template('check_report.html', site=site, project=project, project_ITP=project_ITP, deliverable=deliverable, ITC=ITP_ITC, checks=checks)
    return render_pdf(HTML(string=html))

# provide a url to download a report for tickets
@app.route('/site/all/ticekts')
def tickets_report():
    tickets = FlicketTicket.query.all()

    html = render_template('tickets_report.html', tickets=tickets)
    return render_pdf(HTML(string=html))

# provide a url to force a site report to be sent out via emails
@app.route('/site/<sitename>/issues/_send')
def send_report_trigger(sitename):
    site = Site.query.filter_by(name=sitename).one()
    send_report(site)
    return redirect(url_for('unresolved_list', sitename=site.name))

# output the report as a html object
def generate_report_html(site):
    assets = Asset.query.filter_by(site=site).order_by(Asset.priority.asc()).all()
    recent_results = {}
    unresolved_results = {}
    for asset in assets:
        recent_results[asset] = Result.query.filter_by(asset=asset, recent=True).all()
        unresolved_results[asset] = Result.query.filter(Result.asset==asset, (Result.active == True) | (Result.acknowledged == False)).all()
    # render as raw html
    html_string = render_template('report.html', assets=assets, site=site, recent_results=recent_results, unresolved_results=unresolved_results)
    return HTML(string=html_string)

# output the report in pdf format
def generate_report_pdf(site):
    # first generate html, then convert to pdf
    html = generate_report_html(site)
    return html.write_pdf()

# send a report to the event handler for every site
def send_all_reports():
    # needs to generate a dummy request context for flask_weasyprint to work
    with app.test_request_context():
        for site in Site.query.all():
            send_report(site)

# send a report for a single site
def send_report(site):
    report = generate_report_pdf(site)
    event.handle_report(report, site)
