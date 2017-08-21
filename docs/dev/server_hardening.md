# Server hardening

Security is paramount. Follow these steps to ensure servers are as secure as possible.

## All servers
[This article](https://www.codelitt.com/blog/my-first-10-minutes-on-a-server-primer-for-securing-ubuntu/) is a good starter checklist. Some items, such as firewall are not applicable because they are handled by EC2 Security Groups.

Never hard-code credentials, even while, testing, in a git project repository, always follow the [app configuration](configuration) guidelines.

### SSH
- public key authentication only
- not root access
```
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
```

### fail2ban
```
sudo apt-get install fail2ban
```
TODO: fill out explicit instructions

### logwatch
```
sudo apt-get install logwatch
```
TODO: fill out explicit instructions

## Production servers
TODO: fill out explicit instructions
- Security Group config, accept incoming HTTP connnections from load balancer (ELB) or CDN (CloudFront) only.
- Configure load balancer (ELB)/CDN (CloudFront) to accept HTTPS connections only.

## Development servers
### nginx
- Change nginx listening port from 80 to non-standard, eg: 8888
- Change server name to elastic IP address.
```
# /etc/nginx/sites-available/medusa
server {
    listen 8888;
    server_name [ip address];
    ...
}
```

### DNS
 Delete any DNS records pointing any subdomains to the dev server.

### EC2 Security Group
- Use the medusa-dev Security Group:
![medusa-dev EC2 security group](img/dev-server-ec2-sec-group.png)

### Poweroff when not in use
Reduces exposure (and saves running costs)!

When finished for the day:
```
sudo poweroff
```
Power on using AWS Console or programmatically using `awscli`.
