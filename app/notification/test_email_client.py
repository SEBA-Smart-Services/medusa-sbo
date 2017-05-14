import configparser
from emailClient import EmailClient
#create ConfigParser object
config = configparser.ConfigParser()

#read in config from configfiles
config_file_path = '/var/www/medusa/config.ini'
master_config = config_file_path
config.read(master_config)
main_config = config.get('paths', 'emailConfig')
config.read(main_config)


print("testing")
sender = "medusa@sebbqld.com"
recipient = "christopher.vasiliou@gmail.com"
attachments = ['/var/www/medusa1.pdf', '/var/www/medusa2.pdf']

print("sender: " + sender)
print("recipient: " + recipient)
print("username: " + config.get('emailClient', 'username'))
print("password: " + config.get('emailClient', 'password'))
print("host: " + config.get('emailClient', 'host'))
print("port: " + config.get('emailClient', 'port'))

message_body = "this is a test"
subject = "test email"

client = EmailClient(config_file_path, 'medusa@sebbqld.com')
client.set_host(config.get('emailClient', 'host'), config.get('emailClient', 'port'))
client.set_auth(config.get('emailClient', 'username'), config.get('emailClient', 'password'))
client.set_sender(sender)
client.set_recipients(recipient)
client.write_message(message_body, subject, attachments)
client.sendmail()
