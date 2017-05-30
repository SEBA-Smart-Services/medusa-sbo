## general setup
required apt-get update before other packages could be installed
check permissions for /var/www/medusa, /var/lib/medusa folder
set timezone to brisbane
    sudo ln -sf /usr/share/zoneinfo/Australia/Brisbane /etc/localtime

## configuration files
in .bashrc:
    alias python=python3
    alias pip=pip3

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
create /var/lib/medusa directory (home for config files)
create /etc/systemd/system/medusa.service
create /etc/systemd/system/medusa-config.service

## logging
check permissions on log file at /var/log/uwsgi/medusa.log

## Weasyprint
Weasyprint is used for generating PDF reports.

Deployment of Weasyprint on a new server requires the installation of several packages via apt-get, as well as standard pip install. Documentation for this install can be found here: http://weasyprint.readthedocs.io/en/latest/install.html
Do:
sudo apt-get install libxml2-dev libxslt1-dev libffi-dev
sudo apt-get install python3-lxml python3-cffi libcairo2 libpango1.0-0 libgdk-pixbuf2.0-0 shared-mime-info

## Deploying to production
on local machine:
git pull
git merge origin/sprint_X
git push
on prod server:
git pull
if changed, copy any .service files to systemd folder
systemctl stop medusa/medusa-data-importer
systemctl daemon-reload
pip install -r requirements.txt in virtualenv for both medusa and medusa-data-importer
set environmental variable: export MEDUSA_CONFIG=/var/lib/medusa/medusa-production.ini (only applies to this shell session)
ensure latest config files have been downloaded: systemctl start medusa-config
in medusa virtualenv:
    python3 manage.py db upgrade
systemctl start medusa/medusa-data-importer
