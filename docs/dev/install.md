# First Time Install

## Initial setup
Update the package lists, as some packages need to be installed
`sudo apt-get update`

Create and set permissions for medusa folders and files
```
sudo mkdir /var/www/medusa
sudo chown www-data:www-data /var/www/medusa
sudo chmod 775 /var/www/medusa
sudo mkdir /var/lib/medusa
sudo chown www-data:www-data /var/lib/medusa
sudo chmod 775 /var/lib/medusa
sudo mkdir /var/log/uwsgi
sudo chown www-data:www-data /var/log/uwsgi
sudo chmod 775 /var/log/uwsgi
sudo touch /var/log/uwsgi/medusa.log
sudo chown www-data:www-data /var/log/uwsgi/medusa.log
sudo chmod 775 /var/log/uwsgi/medusa.log
```

Set timezone to brisbane
`sudo ln -sf /usr/share/zoneinfo/Australia/Brisbane /etc/localtime`

## Edit linux configuration files
Add to .bashrc:
```
alias python=python3
alias pip=pip3
```

## Download project from Git
`git clone https://github.com/SEBA-Smart-Services/medusa-sbo.git /var/www/medusa/`

## Install and configure Nginx
Install the package
`sudo apt-get install nginx`

Add the medusa config file. If necessary, edit server_name to match the url being used
`cp /var/www/medusa/docs/ec2conf/etc/nginx/sites-available/medusa /etc/nginx/sites-available/medusa`

Symlink the file to enable it
`sudo ln -s /etc/nginx/sites-available/medusa /etc/nginx/sites-enabled`

## Install Weasyprint requirements
Weasyprint is used for generating PDF reports.

Deployment of Weasyprint on a new server requires the installation of several packages via apt-get, as well as standard pip install. Documentation for this install can be found here: http://weasyprint.readthedocs.io/en/latest/install.html

For ubuntu 16.04 LTS:
```
sudo apt-get install libxml2-dev libxslt1-dev libffi-dev
sudo apt-get install python3-lxml python3-cffi libcairo2 libpango1.0-0 libgdk-pixbuf2.0-0 shared-mime-info
```

## Install pip and download modules
Download packages for pip
```
sudo apt-get install python3-dev python3-pip
sudo apt-get install libmysqlclient-dev
```

Create a virtualenv
```
sudo pip install virtualenv
sudo virtualenv -p python3 /var/www/medusa/env
```

Activate virtualenv and download modules
```
source /var/www/medusa/env/bin/activate
pip install -r requirements.txt
```

## Configure services
Medusa uses a primary service that runs uWSGI, and a secondary service to download an updated config file from S3.
```
sudo cp /var/www/medusa/docs/ec2conf/etc/systemd/system/medusa.service /etc/systemd/system/medusa.service
sudo cp /var/www/medusa/docs/ec2conf/etc/systemd/system/medusa-config.service /etc/systemd/system/medusa-config.service

```

# Deploying to production
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
