from deploy_ses_notifier import IAM_user

AccessKeyID = "AKIAIFZ67S3NUJ6HEOEQ"
SecretAccessKey = "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"

new_user = IAM_user()
new_user.set_SecretAccessKey(SecretAccessKey)
new_user.hash_SmtpPassword()
print(new_user.SmtpPassword)
