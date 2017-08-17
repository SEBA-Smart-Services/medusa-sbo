import boto3

# this file is called by medusa-config.service, which runs every time medusa.service or medusa-data-importer.service are run
# download config from s3

S3_RESOURCE = 's3'
BUCKET_NAME = 'medusa-sebbqld'
BUCKET_CONFIG_DIR = 'config/'
LOCAL_CONFIG_DIR = '/var/lib/medusa/'

s3 = boto3.resource(S3_RESOURCE)

CONFIG_FILES = [
    'medusa-production.cfg',
    'medusa-development.cfg',
    'medusa-testing.cfg',
    'uwsgi-production.ini',
    'uwsgi-development.ini',
    'uwsgi-production.ini',
    'uwsgi-testing.ini',
    'dataimporter-production.ini',
    'dataimporter-testing.ini',
    'dataimporter-development.ini'
]

for config_file in CONFIG_FILES:
    try:
        s3.meta.client.download_file(
            BUCKET_NAME,
            BUCKET_CONFIG_DIR + config_file,
            LOCAL_CONFIG_DIR + config_file
        )
        print('Downloaded ' + config_file)
    except:
        print('Failed to download ' + config_file)

