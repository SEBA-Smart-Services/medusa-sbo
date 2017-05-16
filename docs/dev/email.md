# Email setup

## AWS CLI config
[Setup AWS CLI](awscli.md) on your dev machine.

## Configure DNS
In Domain Registrar, add a CNAME record:
```
host: smtp
value: email-smtp.us-west-2.amazonaws.com
```

## Create SES IAM user/s
Use AWS CLI...
TODO: finish this document
