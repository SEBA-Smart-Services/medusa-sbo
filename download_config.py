import boto3
import os

# this file is called by medusa-config.service, which runs every time medusa.service or medusa-data-importer.service are run
# download config from s3

S3_RESOURCE = 's3'
BUCKET_NAME = 'medusa-sebbqld'
BUCKET_CONFIG_DIR = 'config'
LOCAL_CONFIG_DIR = '/var/lib/medusa'

s3 = boto3.resource(S3_RESOURCE)
s3_client = boto3.client(S3_RESOURCE)

def list_files(client, resource, bucket, source, local):
    # create S3 paginator object
    paginator = client.get_paginator('list_objects')
    # file list to download_dir
    files = []
    # paginate through list of files in bucket using pagintor
    for result in paginator.paginate(Bucket=bucket, Delimiter='/', Prefix=source):
        # check if this file is actually a subdir
        if result.get('CommonPrefixes') is not None:
            # if this is a subdir, execute this function on contents
            for subdir in result.get('CommonPrefixes'):
                nested_files = list_files(client, resource, bucket, subdir.get('Prefix'), local)
                files.extend(nested_files)
        # check if page result has content
        if result.get('Contents') is not None:
            # loop through files in page result
            for file in result.get('Contents'):
                # download file
                # dont try and copy directories, files only
                # (if key has trailing '/' then its a dir)
                if file.get('Key')[-1] != '/':
                    files.append(file.get('Key'))
    return files

def download_dir(client, resource, bucket, source, local):
    files = list_files(client, resource, bucket, source, local)
    print('\ndownloading files:')
    for full_path in files:
        # trim off the source path
        print('\n')
        rel_path = full_path[len(source)+1:]
        # create local destination path
        dest_path = local + os.sep + rel_path
        print(rel_path)
        print(dest_path)
        # if file is in subdir/s, make matching local dir if not exists
        local_dir = os.path.dirname(dest_path)
        print(local_dir)
        if not os.path.exists(local_dir):
            print('PATH DOESNT EXIST, MAKING!')
            os.makedirs(local_dir)
        try:
            resource.meta.client.download_file(
                bucket,
                full_path,
                dest_path
            )
            print('SUCCESS')
        except:
            print('FAIL')

download_dir(s3_client, s3, BUCKET_NAME, BUCKET_CONFIG_DIR, LOCAL_CONFIG_DIR + '/test')
