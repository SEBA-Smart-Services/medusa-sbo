import boto3
import json
from app import app


AWS_ACCESS_KEY_ID = app.config['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = app.config['AWS_SECRET_ACCESS_KEY']
AWS_S3_UPLOADER_IAM_GROUP = app.config['AWS_S3_UPLOADER_IAM_GROUP']
AWS_S3_UPLOADER_IAM_USERNAME_BASE = app.config['AWS_S3_UPLOADER_IAM_USERNAME_BASE']


class AwsIamManager(object):

    def __init__(self, site_id):
        self.aws_s3_uploader_iam_username = self.make_iam_username(site_id)
        self.create_iam_client()

    def make_iam_username(self, site_id):
        return '-'.join([
            AWS_S3_UPLOADER_IAM_USERNAME_BASE,
            str(site_id)
        ])

    def create_iam_client(self):
        self.client = boto3.client(
            'iam',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )

    def check_200_resp(self, resp):
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

    def create_user(self):
        """
        create IAM user and add to IAM group
        """
        # list current IAM users
        resp = self.client.list_users()
        success =  self.check_200_resp(resp)

        if success:
            users = resp['Users']
            # check if user with username already exists
            user_exists = any(user['UserName'] == self.aws_s3_uploader_iam_username for user in users)
            # create user if not exist
            if not user_exists:
                app.logger.info('Creating IAM user %s', self.aws_s3_uploader_iam_username)
                resp = self.client.create_user(UserName=self.aws_s3_uploader_iam_username)
                success =  self.check_200_resp(resp)
                if success:
                    app.logger.info('SUCCESS!')
                # add user to group
                app.logger.info('Adding IAM user %s to group %s' % (self.aws_s3_uploader_iam_username, AWS_S3_UPLOADER_IAM_GROUP))
                resp = self.client.add_user_to_group(
                    GroupName=AWS_S3_UPLOADER_IAM_GROUP,
                    UserName=self.aws_s3_uploader_iam_username
                )
                success =  self.check_200_resp(resp)
                if success:
                    app.logger.info('SUCCESS!')
            else:
                app.logger.info('Tried to creating IAM user %s but username already exists.', self.aws_s3_uploader_iam_username)
                success = False
        return {
            "user_name": self.aws_s3_uploader_iam_username,
            "group_name": AWS_S3_UPLOADER_IAM_GROUP,
            "success": success
        }

    def create_access_key(self):
        """
        create acess key for IAM user
        """
        app.logger.info('Creating access key for user %s' % self.aws_s3_uploader_iam_username)
        resp = self.client.create_access_key(
            UserName=self.aws_s3_uploader_iam_username
        )
        success =  self.check_200_resp(resp)
        # print(create_access_key_resp)
        if success:
            app.logger.info('SUCCESS!')
            # self.secret_access_key = resp['User']['UserName'])
            access_key_username = resp['AccessKey']['UserName']
            self.access_key_status = resp['AccessKey']['Status']
            self.secret_access_key = resp['AccessKey']['SecretAccessKey']
            self.access_key_id = resp['AccessKey']['AccessKeyId']
        else:
            self.secret_access_key = None
            self.access_key_id = None
            self.access_key_status = None
        return {
            "aws_secret_access_key": self.secret_access_key,
            "aws_access_key_id": self.access_key_id,
            "aws_iam_username": self.aws_s3_uploader_iam_username,
            "aws_access_key_status": self.access_key_status,
            "success": success
        }

    def delete_user(self):
        app.logger.info('Removing IAM user %s from group %s ' % (self.aws_s3_uploader_iam_username, AWS_S3_UPLOADER_IAM_GROUP))
        try:
            resp = self.client.remove_user_from_group(
            GroupName=AWS_S3_UPLOADER_IAM_GROUP,
            UserName=self.aws_s3_uploader_iam_username
            )
            success = self.check_200_resp(resp)
        except:
            success = False

        app.logger.info('Deleting IAM user %s' % self.aws_s3_uploader_iam_username)
        if success:
            app.logger.info('SUCCESS!')
        try:
            resp = self.client.delete_user(UserName=self.aws_s3_uploader_iam_username)
            success = self.check_200_resp(resp)
            if success:
                app.logger.info('SUCCESS!')
        except:
            success = False
        return success

    def delete_access_key(self):
        app.logger.info('Listing access keys for user %s ' % self.aws_s3_uploader_iam_username)
        try:
            resp = self.client.list_access_keys(UserName=self.aws_s3_uploader_iam_username)
            success = self.check_200_resp(resp)
            if success:
                app.logger.info('SUCCESS!')
                for access_key in resp['AccessKeyMetadata']:
                    app.logger.info('deleting access key %s for user %s ' % (access_key['AccessKeyId'], self.aws_s3_uploader_iam_username))
                    resp = self.client.delete_access_key(
                    UserName=self.aws_s3_uploader_iam_username,
                    AccessKeyId=access_key['AccessKeyId']
                    )
                    success = self.check_200_resp(resp)
                    if success:
                        app.logger.info('SUCCESS!')
                        return success
        except:
            return False
