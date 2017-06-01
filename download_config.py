import boto3

# this file is called by medusa-config.service, which runs every time medusa.service or medusa-data-importer.service are run
# download config from s3
s3 = boto3.resource('s3')
s3.meta.client.download_file('medusa-sebbqld', 'config/medusa-development.ini', '/var/lib/medusa/medusa-development.ini')
s3.meta.client.download_file('medusa-sebbqld', 'config/medusa-production.ini', '/var/lib/medusa/medusa-production.ini')
