# Setting up an Elastic Load Balancer

## Creation

1. From the AWS console go to EC2 and click on **Load Balancers** under the *Load balancing* tab.
2. Click **Create Load Balancer** and cerate a new *Application Load Balancer*.
3. Give the new ELB a unique name and make sure it is internet-facing.
4. Based on the way Medusa has been constructed only HTTP listeners are required as the CDN handles the HTTPS requests.
The ELB will handle any traffic between the CDN and the EC2 instances when attached.
5. At least 2 availability zones need to be selected. Select *Next* to head to security settings.
6. As we are not handling any HTTPS requests we do not need to set up any security settings for this part. Select *Next* for group security settings.
7. The new ELB should follow the same rules as the *prod-lb* security group which has already been setup. Select *Next* for target group creation.
8. A target group is a set of rules on how to send traffic to a group of targets (EC2 instances in this case). For our purposes the default (HTTP on port 80
with a instance target) is fine, so just give the target group a name. 
9. The Health check is just to verify that the target instance is still running correctly. The path will specify what page it uses to test
the healthyness of a target, leaving it as '/' is fine for now. Click *Next* to add instances to the target group.
10. Select the instances you want to add to this ELB (Each instance can only be registered to one ELB), any traffic sent to the ELB will now be distributed
to these attached instances as long as they remain healthy. 
11. Click *Next* and review all the settings, once they are correct click **Create**. It may take 10-15min for the Load Balancer to be created
but once it is you should be able to go to it's URL (DNS) and see the medusa app running (or whatever you have attached to the ELB)
12. The next steps are to set up the load balancer so it only takes traffic from the CDN and the instances only listen for traffic from the ELB.

## Attaching more instances

TODO

## Configure ELB Settings

TODO

## Configure Instance Settings

TODO
