## general setup
required apt-get update before other packages could be installed
check permissions for medusa folder

## configuration files
in .bashrc:
    alias python=python3
    alias pip=pip3
create /var/lib/medusa/emailConfig.ini

## Nginx
sudo apt-get install nginx
add medusa config file to /etc/nginx/sites-available, edit server_name
sudo ln -s /etc/nginx/sites-available/medusa /etc/nginx/sites-enabled

## Git
sudo git clone https://github.com/SEBA-Smart-Services/medusa-sbo.git /var/www/medusa/
manually copy /var/www/medusa/config.py

## python pip
sudo apt-get install python3-dev python3-pip
sudo apt-get install libmysqlclient-dev
create virtualenv
    sudo pip install virtualenv
    sudo virtualenv -p python3 /var/www/medusa/env
inside virtualenv:
    sudo pip install -r requirements.txt

## uwsgi
create /etc/systemd/system/medusa.service

## logging
check permissions on log file at /var/log/uwsgi/medusa.log

## Weasyprint
Weasyprint is used for generating PDF reports.

Deployment of Weasyprint on a new server requires the installation of several packages via apt-get, as well as standard pip install. Documentation for this install can be found here: http://weasyprint.readthedocs.io/en/latest/install.html

sudo apt-get install libxml2-dev libxslt1-dev libffi-dev
sudo apt-get install python3-lxml python3-cffi libcairo2 libpango1.0-0 libgdk-pixbuf2.0-0 shared-mime-info
