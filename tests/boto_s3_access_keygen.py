import os
import configparser
import boto3
import json


def check_200_resp(resp):
    """
    check AWS response to boto3 request is successful
    """
    try:
        if resp['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False
    except:
        return False

# FAKE SITE ID FOR TESTING
SITE_ID = 69


SETTINGS = 'MEDUSA_DEVELOPMENT_SETTINGS'
SETTINGS_PATH = os.environ[SETTINGS]
# arbitrary fake section name required for configparser to parse the section-less config file
SECTION = 'AWS'
with open(SETTINGS_PATH, 'r') as f:
    config_string = '[' + SECTION + ']\n' + f.read()

config = configparser.ConfigParser()
config.read_string(config_string)

AWS_ACCESS_KEY_ID = config.get(SECTION, 'AWS_ACCESS_KEY_ID').strip('"')
AWS_SECRET_ACCESS_KEY = config.get(SECTION, 'AWS_SECRET_ACCESS_KEY').strip('"')
AWS_S3_UPLOADER_IAM_GROUP = config.get(SECTION, 'AWS_S3_UPLOADER_IAM_GROUP').strip('"')
AWS_S3_UPLOADER_IAM_USERNAME_BASE = config.get(SECTION, 'AWS_S3_UPLOADER_IAM_USERNAME_BASE').strip('"')
AWS_S3_UPLOADER_IAM_USERNAME = '-'.join([
    AWS_S3_UPLOADER_IAM_USERNAME_BASE,
    str(SITE_ID)
])

################################################################################
# test S3
s3 = boto3.resource(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Print out bucket names
for bucket in s3.buckets.all():
    print(bucket.name)

################################################################################
# test IAM
iam = boto3.client(
    'iam',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

print('\Listing IAM users...')
list_users_resp = iam.list_users()
success =  check_200_resp(list_users_resp)
if success:
    print('FUCKING SUCCESS!!!')
####
# warning: no pagination support, consider using when IAM user count grows
# look for the Marker element
####
success =  check_200_resp(list_users_resp)
if success:
    users = list_users_resp['Users']
    for user in users:
        print(user['UserName'])
    user_exists = any(user['UserName'] == AWS_S3_UPLOADER_IAM_USERNAME for user in users)
    print(AWS_S3_UPLOADER_IAM_USERNAME, user_exists)
    if not user_exists:
        print('\nCreating IAM user: ' + AWS_S3_UPLOADER_IAM_USERNAME + ' ...')
        create_user_resp = iam.create_user(UserName=AWS_S3_UPLOADER_IAM_USERNAME)
        # print(create_user_resp)
        print(create_user_resp['User']['UserName'])
        success =  check_200_resp(create_user_resp)
        if success:
            print('FUCKING SUCCESS!!!')
        print('\nAdding IAM user ' + AWS_S3_UPLOADER_IAM_USERNAME + ' to group: ' + AWS_S3_UPLOADER_IAM_GROUP + ' ...')
        add_user_to_group_resp = iam.add_user_to_group(
            GroupName=AWS_S3_UPLOADER_IAM_GROUP,
            UserName=AWS_S3_UPLOADER_IAM_USERNAME
        )
        # print(add_user_to_group_resp)
        if success:
            print('FUCKING SUCCESS!!!')


print('\nCreating access key for user: ' + AWS_S3_UPLOADER_IAM_USERNAME + ' ...')
create_access_key_resp = iam.create_access_key(
    UserName=AWS_S3_UPLOADER_IAM_USERNAME
)
print(create_user_resp['User']['UserName'])
print(create_access_key_resp['AccessKey']['UserName'])
print(create_access_key_resp['AccessKey']['Status'])
print(create_access_key_resp['AccessKey']['SecretAccessKey'])
print(create_access_key_resp['AccessKey']['AccessKeyId'])
# print(create_access_key_resp)
success =  check_200_resp(create_access_key_resp)
# print(create_access_key_resp)
if success:
    print('FUCKING SUCCESS!!!')

# print(response, type(response))
print('\nlisting access keys for user: ' + AWS_S3_UPLOADER_IAM_USERNAME + ' ...')
if success:
    list_access_keys_resp = iam.list_access_keys(UserName=AWS_S3_UPLOADER_IAM_USERNAME)
success = check_200_resp(list_access_keys_resp)
# print(list_access_keys_resp)
if success:
    print('FUCKING SUCCESS!!!')

if success:
    for access_key in list_access_keys_resp['AccessKeyMetadata']:
        print('\ndeleting access key: ' + access_key['AccessKeyId'] + ' ...')
        delete_access_key_resp = iam.delete_access_key(
            UserName=AWS_S3_UPLOADER_IAM_USERNAME,
            AccessKeyId=access_key['AccessKeyId']
        )
        # print(delete_access_key_resp)
        success = check_200_resp(delete_access_key_resp)
        if success:
            print('FUCKING SUCCESS!!!')

print('\nRemoving IAM user: ' + AWS_S3_UPLOADER_IAM_USERNAME + ' from group: ' + AWS_S3_UPLOADER_IAM_GROUP + ' ...')
remove_user_from_group_resp = iam.remove_user_from_group(
    GroupName=AWS_S3_UPLOADER_IAM_GROUP,
    UserName=AWS_S3_UPLOADER_IAM_USERNAME
)
success = check_200_resp(remove_user_from_group_resp)
# print(remove_user_from_group_resp)
if success:
    print('FUCKING SUCCESS!!!')
if success:
    print('\nDeleting IAM user: ' + AWS_S3_UPLOADER_IAM_USERNAME + ' ...')
    delete_user_resp = iam.delete_user(UserName=AWS_S3_UPLOADER_IAM_USERNAME)
    success = check_200_resp(delete_user_resp)
    # print(delete_user_resp)
    if success:
        print('FUCKING SUCCESS!!!')
