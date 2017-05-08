import configparser
from emailClient import EmailClient
#create ConfigParser object
config = configparser.ConfigParser()

#read in config from configfiles
master_config = 'config.ini'
config.read(master_config)
main_config = config.get('paths', 'emailConfig')
config.read(main_config)


print("testing")
sender = "medusa@sebbqld.com"
recipient = "Daniel.Marshall@schneider-electric.com"

print("sender: " + sender)
print("recipient: " + recipient)
print("username: " + config.get('emailClient', 'username'))
print("password: " + config.get('emailClient', 'password'))
print("host: " + config.get('emailClient', 'host'))
print("port: " + config.get('emailClient', 'port'))

message_body = "this is a test"
subject = "test email"

client = EmailClient()
client.set_host(config.get('emailClient', 'host'), config.get('emailClient', 'port'))
client.set_auth(config.get('emailClient', 'username'), config.get('emailClient', 'password'))
client.set_sender(sender)
client.set_recipients(recipient)
client.write_message(message_body, subject)
client.sendmail()
