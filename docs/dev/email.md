# Email setup

## AWS CLI config
In AWS Console, create IAM user with CLI access. Be restrictive! Generate access key.

Install AWS CLI:
```
pip insall awscli
```

Then configure AWS CLI:
```
aws configure
```
Enter IAM user access key.

## Configure DNS
In Domain Registrar, add a CNAME record:
```
host: smtp
value: email-smtp.us-west-2.amazonaws.com
```

## Create SES IAM user/s
Use AWS CLI...
TODO: finish this document
