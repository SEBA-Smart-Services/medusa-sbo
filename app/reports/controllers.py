from app import app, event, manager
from app.models import Site, Asset, Result
from app.models.ITP import Project, ITP, Deliverable, Deliverable_ITC_map, Deliverable_check_map, Deliverable_type, ITC_group
from app.ticket.models import FlicketTicket
from flask import render_template, request, jsonify, url_for, redirect, make_response, send_file, send_from_directory, after_this_request
from flask_weasyprint import HTML, CSS, render_pdf
import datetime
from app import celery
import os

from jinja2 import Environment, PackageLoader, select_autoescape
import weasyprint
import time
from flask_script import prompt_choices, prompt_bool
from PyPDF2 import PdfFileMerger, PdfFileReader
import json

import pdfkit

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

    return render_template('loading_page.html', site=site, project=project, ITP=project_ITP, deliverable_types=deliverable_types)

# provide a url to download a report for Deliverabels
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/Deliverables/report')
def deliverables_report_page(siteid, projectid, ITPid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid).first()
    project_ITP = ITP.query.filter_by(id=ITPid).first()
    deliverables = Deliverable.query.filter_by(ITP_id=project_ITP.id).all()
    deliverable_types = Deliverable_type.query.filter(Deliverable_type.id.in_([deliverable.deliverable_type_id for deliverable in deliverables])).all()

    return render_template('Deliverable_loading_page.html', site=site, project=project, ITP=project_ITP, deliverables=deliverables, deliverable_types=deliverable_types)

#Downloads the report
@app.route('/<siteid>/<projectid>/<ITPid>/download_report')
def download_report(siteid, projectid, ITPid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid).first()
    project_ITP = ITP.query.filter_by(id=ITPid).first()

    # name = str(site.name).replace(" ","_") + '_' + str(project.name).replace(" ","_") + '_' + time.strftime("%Y%m%d") + '.pdf'
    name = 'test_plan.pdf'

    print(ITP.percentage_complete)

    @after_this_request
    def remove_file(response):
        try:
            os.remove(app.config['PROJECT_ROOT'] + '/app/reports/' + name)
        except Exception as error:
            app.logger.error("Error removing or closing downloaded file handle", error)
        return response
    return send_file('reports/' + name, as_attachment=True)

#Downloads the report
@app.route('/<siteid>/<projectid>/<ITPid>/download_deliverable_report')
def download_Deliverable_report(siteid, projectid, ITPid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid).first()
    project_ITP = ITP.query.filter_by(id=ITPid).first()

    # name = str(site.name).replace(" ","_") + '_' + str(project.name).replace(" ","_") + '_' + time.strftime("%Y%m%d") + '.pdf'
    name = 'test_deliverables.pdf'
    @after_this_request
    def remove_file(response):
        try:
            os.remove(app.config['PROJECT_ROOT'] + '/app/reports/' + name)
        except Exception as error:
            app.logger.error("Error removing or closing downloaded file handle", error)
        return response
    return send_file('reports/' + name, as_attachment=True)

#starts the pdf generation
@app.route('/longtask', methods=['POST'])
def longtask():
    siteid = request.form['siteid']
    projectid = request.form['projectid']
    ITPid = request.form['ITPid']
    print(siteid)
    print(projectid)
    print(ITPid)
    print("starting background task")
    pdf = ITP_report_pdf_render.delay(siteid=siteid, projectid=projectid, ITPid=ITPid)
    return jsonify({}), 202, {'Location': url_for('taskstatus', task_id=pdf.id)}

#starts the pdf generation
@app.route('/longtaskDeliverables', methods=['POST'])
def longtaskDeliverables():
    siteid = request.form['siteid']
    projectid = request.form['projectid']
    ITPid = request.form['ITPid']
    deliverableIdList = list(map(int, json.loads(request.form['deliverableIdList'])))
    print(siteid)
    print(projectid)
    print(ITPid)
    print(deliverableIdList)
    print("starting background task")
    pdf = Deliverables_report_pdf_render.delay(siteid=siteid, projectid=projectid, ITPid=ITPid, deliverableIdList=deliverableIdList)
    return jsonify({}), 202, {'Location': url_for('taskstatus', task_id=pdf.id)}

#checks the current status for the generated report
@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = ITP_report_pdf_render.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': 'Complete'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info['current'],
            'total': task.info['total'],
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)

#Asynchronus task that will create the ITP report PDF
@celery.task(bind=True)
def ITP_report_pdf_render(self, siteid, projectid, ITPid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid).first()
    project_ITP = ITP.query.filter_by(id=ITPid).first()
    deliverables_all = Deliverable.query.filter_by(ITP_id=project_ITP.id).all()
    deliverables = Deliverable.query.filter_by(ITP_id=project_ITP.id).all()
    deliverable_types = Deliverable_type.query.filter(Deliverable_type.id.in_([deliverable.deliverable_type_id for deliverable in deliverables])).all()
    deliverable_types_all = Deliverable_type.query.filter(Deliverable_type.id.in_([deliverable.deliverable_type_id for deliverable in deliverables_all])).all()
    today = datetime.datetime.now()
    # image = flask_weasyprint.default_url_fetcher("/static/img/logo-schneider-electric.png")
    ITC_groups = ITC_group.query.all()
    ITC_groups = sorted(ITC_groups, key=lambda x: x.name)

    self.update_state(state='PROGRESS')

    DDC_group = ['Automation Server', 'AS-P', 'AS']

    #Set up variables to update user screen while ITCs are generated
    i = 0
    total = len(deliverables) + len(deliverables)

    ITCs = Deliverable_ITC_map.query.filter(Deliverable_ITC_map.deliverable_id.in_([deliverable.id for deliverable in deliverables])).all()
    ITCs = sorted(ITCs, key=lambda x: (x.deliverable.type.name, x.deliverable.name, x.ITC.group.name))
    i += total * 0.1
    self.update_state(state='PROGRESS', meta={'current': i, 'total': total, 'status': 'Creating ITCs'})

    print('ITCs have been created')
    ITCs_old = sorted(ITCs, key=lambda x: (x.ITC.group.name))
    i += total * 0.1
    self.update_state(state='PROGRESS', meta={'current': i, 'total': total, 'status': 'Creating ITCs'})

    env = Environment(
    loader=PackageLoader('app', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
    )

    i += total * 0.05
    self.update_state(state='PROGRESS',
                      meta={'current': i, 'total': total, 'status': 'Starting Report build'})

    #create from pages
    name = 'ITP_base.pdf'

    #Creates PDF
    with app.app_context():
        template = render_template( 'ITP_report_base.html',
                                    site=site,
                                    project=project,
                                    project_ITP=project_ITP,
                                    deliverables=deliverables,
                                    deliverables_all=deliverables_all,
                                    ITCs=ITCs,
                                    deliverable_types=deliverable_types,
                                    deliverable_types_all=deliverable_types_all,
                                    today=today,
                                    groups=ITC_groups,
                                    DDC_group=DDC_group)

        print('Start pdf template rendered')
        i += total * 0.025
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total, 'status': 'Starting Report build'})

        html = weasyprint.HTML(string=template)
        pdf = html.write_pdf('./' + name)

        print('converting to pdf')

        percent_add = len(deliverables) / total

        #create deliverable pdfs
        for x in range(len(deliverables)):
            name = 'pdf_' + str(x) + '.pdf'
            deliverable = deliverables[x]

            #Creates PDF
            template = render_template( 'ITP_report.html',
                                        site=site,
                                        project=project,
                                        project_ITP=project_ITP,
                                        deliverable=deliverable,
                                        deliverables=deliverables,
                                        deliverables_all=deliverables_all,
                                        ITCs=ITCs,
                                        deliverable_types=deliverable_types,
                                        deliverable_types_all=deliverable_types_all,
                                        today=today,
                                        groups=ITC_groups,
                                        DDC_group=DDC_group)

            i += percent_add
            self.update_state(state='PROGRESS', meta={'current': i, 'total': total, 'status': 'Creating ITCs'})

            print('Middle pdf templates rendered')

            html = weasyprint.HTML(string=template)
            pdf = html.write_pdf('./' + name)

            print('converting to pdf')

        #Create final part of report
        template = render_template( 'ITP_report_end.html',
                                    site=site,
                                    project=project,
                                    project_ITP=project_ITP,
                                    deliverables=deliverables,
                                    deliverables_all=deliverables_all,
                                    ITCs=ITCs,
                                    deliverable_types=deliverable_types,
                                    deliverable_types_all=deliverable_types_all,
                                    today=today,
                                    groups=ITC_groups,
                                    DDC_group=DDC_group)

        name = 'ITP_report_end.pdf'
        i += total * 0.025
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total, 'status': 'Starting Report build'})

        print('Final pdf template rendered')

        html = weasyprint.HTML(string=template)
        pdf = html.write_pdf('./' + name)

        print('converting to pdf')

    pdf_number = x + 1

    #join pdfs
    pdfs = ['ITP_base.pdf']
    for y in range(pdf_number):
        pdfs.extend(['pdf_' + str(y) + '.pdf'])

    pdfs.extend(['ITP_report_end.pdf'])

    i += len(deliverables) * 0.1
    self.update_state(state='PROGRESS',
                      meta={'current': i, 'total': total, 'status': 'Starting Report build'})

    merger = PdfFileMerger()

    percent_add = len(deliverables) * 0.5 / pdf_number
    for pdf in pdfs:
        merger.append(PdfFileReader(app.config['PROJECT_ROOT'] + '/' + pdf), import_bookmarks=False)
        i += percent_add
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total, 'status': 'Starting Report build'})

    name = 'test_plan.pdf'

    merger.write('app/reports/' + name)
    for pdf in pdfs:
        os.remove(app.config['PROJECT_ROOT'] + '/' + pdf)

    print('page has been rendered')

    self.update_state(state='Complete', meta={'current': total, 'total': total, 'status': 'Complete'})

#Asynchronus task that will create the ITP report PDF
@celery.task(bind=True)
def Deliverables_report_pdf_render(self, siteid, projectid, ITPid, deliverableIdList):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid).first()
    project_ITP = ITP.query.filter_by(id=ITPid).first()
    print(deliverableIdList)
    print([deliverable for deliverable in deliverableIdList])
    deliverables_all = Deliverable.query.filter(Deliverable.id.in_(deliverableIdList)).all()
    deliverables = Deliverable.query.filter(Deliverable.id.in_(deliverableIdList)).all()
    deliverable_types = Deliverable_type.query.filter(Deliverable_type.id.in_([deliverable.deliverable_type_id for deliverable in deliverables])).all()
    deliverable_types_all = Deliverable_type.query.filter(Deliverable_type.id.in_([deliverable.deliverable_type_id for deliverable in deliverables_all])).all()
    today = datetime.datetime.now()
    # image = flask_weasyprint.default_url_fetcher("/static/img/logo-schneider-electric.png")
    ITC_groups = ITC_group.query.all()
    ITC_groups = sorted(ITC_groups, key=lambda x: x.name)

    self.update_state(state='PROGRESS')

    DDC_group = ['Automation Server', 'AS-P', 'AS']

    #Set up variables to update user screen while ITCs are generated
    i = 0
    total = len(deliverables) + len(deliverables)

    ITCs = Deliverable_ITC_map.query.filter(Deliverable_ITC_map.deliverable_id.in_([deliverable.id for deliverable in deliverables])).all()
    ITCs = sorted(ITCs, key=lambda x: (x.deliverable.type.name, x.deliverable.name, x.ITC.group.name))
    i += total * 0.1
    self.update_state(state='PROGRESS', meta={'current': i, 'total': total, 'status': 'Creating ITCs'})

    print('ITCs have been created')
    ITCs_old = sorted(ITCs, key=lambda x: (x.ITC.group.name))
    i += total * 0.1
    self.update_state(state='PROGRESS', meta={'current': i, 'total': total, 'status': 'Creating ITCs'})

    env = Environment(
    loader=PackageLoader('app', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
    )

    i += total * 0.05
    self.update_state(state='PROGRESS',
                      meta={'current': i, 'total': total, 'status': 'Starting Report build'})

    #Creates PDF
    with app.app_context():
        i += total * 0.025
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total, 'status': 'Starting Report build'})

        print('converting to pdf')

        percent_add = len(deliverables) / total

        #create deliverable pdfs
        for x in range(len(deliverables)):
            name = 'pdf_' + str(x) + '.pdf'
            deliverable = deliverables[x]

            #Creates PDF
            template = render_template( 'ITP_report.html',
                                        site=site,
                                        project=project,
                                        project_ITP=project_ITP,
                                        deliverable=deliverable,
                                        deliverables=deliverables,
                                        deliverables_all=deliverables_all,
                                        ITCs=ITCs,
                                        deliverable_types=deliverable_types,
                                        deliverable_types_all=deliverable_types_all,
                                        today=today,
                                        groups=ITC_groups,
                                        DDC_group=DDC_group)

            i += percent_add
            self.update_state(state='PROGRESS', meta={'current': i, 'total': total, 'status': 'Creating ITCs'})

            print('Middle pdf templates rendered')

            html = weasyprint.HTML(string=template)
            pdf = html.write_pdf('./' + name)

            print('converting to pdf')

        i += total * 0.025
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total, 'status': 'Starting Report build'})

    pdf_number = x + 1

    #join pdfs
    pdfs = []
    for y in range(pdf_number):
        pdfs.extend(['pdf_' + str(y) + '.pdf'])

    i += len(deliverables) * 0.1
    self.update_state(state='PROGRESS',
                      meta={'current': i, 'total': total, 'status': 'Starting Report build'})

    merger = PdfFileMerger()

    percent_add = len(deliverables) * 0.5 / pdf_number
    for pdf in pdfs:
        merger.append(PdfFileReader(app.config['PROJECT_ROOT'] + '/' + pdf), import_bookmarks=False)
        i += percent_add
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total, 'status': 'Starting Report build'})

    name = 'test_deliverables.pdf'

    merger.write('app/reports/' + name)
    for pdf in pdfs:
        os.remove(app.config['PROJECT_ROOT'] + '/' + pdf)

    print('page has been rendered')

    self.update_state(state='Complete', meta={'current': total, 'total': total, 'status': 'Complete'})


# provide a url to download a report for all delvierables in an ITP
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/report')
def old_deliverables_report_page(siteid, projectid, ITPid):
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
