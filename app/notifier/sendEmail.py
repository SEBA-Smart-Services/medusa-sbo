import smtplib

user = ""
pw = ""
host = "email-smtp.us-west-2.amazonaws.com"
port = 587
me   = "medusa@sebbqld.com"
you  = ("christopher.vasiliou@schneider-electric.com",)
body = "The gorgon Medusa has risen!! \n Stare into my eyes!"
msg  = ("From: %s\r\nTo: %s\r\n\r\n" % (me, ", ".join(you)))
msg = msg + body
s = smtplib.SMTP(host, port, timeout = 10)
s.starttls()
s.login(user, pw)
s.sendmail(me, you, msg)
s.quit()
