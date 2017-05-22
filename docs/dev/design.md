## services

Medusa uses two systemd services, the code for which is stored in ec2conf/

Medusa.service is the primary uWSGI service. It must be edited to include an environmental variable for the path to the config filed (either medusa-development.ini or medusa-production.ini)

Medusa-config.service is a one-shot service that is automatically triggered before the main one. Its only function is to run a python script that downloads the config files from S3 into the /var/lib/medusa folder. These will be re-downloaded every time the service is restarted. There is a separate config file for dev and prod, each of which contains all config settings (including flask, email and wsgi settings)
