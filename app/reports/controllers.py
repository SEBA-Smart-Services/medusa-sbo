from app import app
from app.models import Site, Asset, Result
from flask import render_template
from flask_weasyprint import HTML, render_pdf

# generate report for a site
@app.route('/site/<sitename>/report')
def report(sitename):
    site = Site.query.filter_by(name=sitename).one()
    assets = Asset.query.filter_by(site=site).all()
    recent_results = {}
    unresolved_results = {}
    for asset in assets:
        recent_results[asset] = Result.query.filter_by(asset=asset, recent=True).all()
        unresolved_results[asset] = Result.query.filter(Result.asset==asset, (Result.active == True) | (Result.acknowledged == False)).all()
    html = render_template('report.html', assets=assets, site=site, recent_results=recent_results, unresolved_results=unresolved_results)
    return render_pdf(HTML(string=html))
