# AWS CLI setup

For AWS infrastructure configuration management from command line.

## Create dedicated IAM user
In AWS Console, create IAM user with CLI access. Be restrictive! Generate access key.

Install AWS CLI:
```
pip insall awscli
```

Then configure AWS CLI:
```
aws configure
AWS Access Key ID [None]: xxxxxxxxxxxxxxxxx
AWS Secret Access Key [None]: xxxxxxxxxxxxxxxxx
Default region name [None]: ap-southeast-2
Default output format [None]: json
```
