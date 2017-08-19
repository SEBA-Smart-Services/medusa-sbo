import os
import configparser
import boto3

SETTINGS = 'MEDUSA_DEVELOPMENT_SETTINGS'
SETTINGS_PATH = os.environ[SETTINGS]
SECTION = 'AWS'
with open(SETTINGS_PATH, 'r') as f:
    config_string = '[' + SECTION + ']\n' + f.read()

config = configparser.ConfigParser()
config.read_string(config_string)

print(config.get(SECTION, 'AWS_ACCESS_KEY_ID'))
print(config.get(SECTION, 'AWS_SECRET_ACCESS_KEY'))

s3 = boto3.resource('s3')

# Print out bucket names
for bucket in s3.buckets.all():
    print(bucket.name)
