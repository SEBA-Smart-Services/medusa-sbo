from deploy_ses_notifier import IAM_user

AccessKeyID = ""
SecretAccessKey = ""

new_user = IAM_user()
new_user.set_SecretAccessKey(SecretAccessKey)
new_user.hash_SmtpPassword()
print(new_user.SmtpPassword)
