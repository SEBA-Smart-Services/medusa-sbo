from app import app, event
from app.models import Site, Asset, Result
from flask import render_template, url_for, redirect
from flask_weasyprint import HTML, render_pdf

# provide a url to download a report for a site
@app.route('/site/<sitename>/report')
def report_page(sitename):
    site = Site.query.filter_by(name=sitename).one()
    html = generate_report_html(site)
    return render_pdf(html)

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
