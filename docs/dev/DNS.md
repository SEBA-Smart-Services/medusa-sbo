# Domain and DNS settings

## Production web server
TODO

### Deploy EC2 instance
TODO

### Assign Elastic IP
TODO

### Configure security group
TODO

### Configure CDN
TODO

### Configure HTTPS
TODO

### Configure load balancer
TODO

### Add DNS record
TODO

## Development web servers
TODO

## SMTP Server

### Overview
Make an SMTP server available at `smtp.mydomain.com`.

### Add DNS record
In Domain Registrar, add a CNAME record:
```
host: smtp
value: email-smtp.us-west-2.amazonaws.com
```
### Create SES IAM user/s
Use AWS CLI...
TODO: finish this document
