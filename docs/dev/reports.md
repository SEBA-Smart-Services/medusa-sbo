# Reporting

Reporting  is another core feature that Medusa brings to the table. To do this Medusa makes use of the weasyprint package which converts html/css to pdfs. There are several pages which use this feature including ITPs, Tickets and Analytics. The weasyprint package is easy to implement and just requires a contorller and template to create them, for customization of the pdfs please refer to the [documentation](http://weasyprint.org/).

## Setup

### Controllers

Controllers for reports can be found under `/app/reports/controllers.py`. The code found here should be relatively simple to follow when creating new reports otherwise follow the documentation above (In addition tutorials can be found [here](http://weasyprint.readthedocs.io/en/stable/tutorial.html)).

### Templates

The templates are located in the `/app/template` folder, moving forward these reports should be moved into their own seperate folder. The templates themselves are like any other template for the web application, just note that mdl styles may not render in weasyprint so it may be better to look through the weasyprint documentation for better report layouts.

##Other

### Sending Reports

In addition to report generation and viewing, reports can also be sent out to a site email through the *send_report* and *send_all_reports* functions using an email client already setup. The emails are first passed to an event handler function (found in `/app/event_handler/event_handler.py`) which passes the data to some methods found in notification (`app/notification/notifier.py` and `/app/notification/emailClient.py`).
