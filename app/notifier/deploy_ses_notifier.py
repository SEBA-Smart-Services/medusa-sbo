import hmac
import hashlib
import base64
import subprocess


class SubprocessCaller(object):

    def __init__(self, command="", std_as_str=True):
        """
        Executes a subprocess using subprocess.Popen

        command: a string command or list of arguments to pass to subprocess.Popen
        std_as_str: if True, concatenate stdout and stderr into a string to return
            instead of the default tuple

        usage:
        >> command = SubprocessCaller("bash command goes here")
        >> output = command.execute()

        """
        self.set_command(command)
        self.std_as_str = std_as_str

    def set_command(self, command):
        if isinstance(command, str):
            self.command = command.split(" ")
        elif isinstance(command, list):
            self.command = command
        else:
            raise Exception("Error: Command must be a string or list")

    def execute(self):
        """
        execute <command> as bash command using subprocess
        use --config switch to explicitly set config file.
        """
        # bash command
        process = subprocess.Popen(
            self.command,
            shell=True, #CV had to add this in to make it work with windows
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # output equals tuple (stdout, stderr)
        # note stderr isnt necessarily error output,
        # may contain standard verbose output from command
        output = process.communicate()
        # if self.std_as_str:
        #     output = self.concat_std(output)
        return output


class IAM_user(object):

    def __init__(self):
        """
        this class is intended to model an IAM user.

        so far, it just takes an IAM user SecretAccessKey and hashes it into an SMTP server password
        """
        self.SecretAccessKey = None
        self.SmtpPassword = None

    def set_SecretAccessKey(self, SecretAccessKey):
        self.SecretAccessKey = SecretAccessKey

    def hash_SmtpPassword(self):

        # only hash if SecretAccessKey has been set
        if self.SecretAccessKey is None:
            print("Failed: No SecretAccessKey, use set_SecretAccessKey()")

        else:

            # http://docs.aws.amazon.com/ses/latest/DeveloperGuide/smtp-credentials.html

            # pseudocode:
            # message = "SendRawEmail";
            # versionInBytes = 0x02;
            # signatureInBytes = HmacSha256(message, key);
            # signatureAndVer = Concatenate(versionInBytes, signatureInBytes);
            # smtpPassword = Base64(signatureAndVer);

        	#private static final String KEY = "AWS SECRET ACCESS KEY";
        	AWS_SECRET_ACCESS_KEY = self.SecretAccessKey

        	# private static final String MESSAGE = "SendRawEmail";
        	AWS_MESSAGE = "SendRawEmail"
        	#in Python 2, str are bytes
        	signature = hmac.new(
        		key=AWS_SECRET_ACCESS_KEY,
        		#byte[] rawSignature = mac.doFinal(MESSAGE.getBytes());
        		msg=AWS_MESSAGE,
        		digestmod=hashlib.sha256
        	).digest()

        	# Prepend the version number to the signature.
        	signature = chr(2) + signature

        	# To get the final SMTP password, convert the HMAC signature to base 64.
        	signature = base64.b64encode(signature)

        	self.SmtpPassword = signature


if __name__ == '__main__':

    user_name = 'medusa_postman'
    group_name = 'medusa_ses_group'
    policy_file = "file://groupPolicy.json"
    policy_name = "medusa-ses-notifier"
    command = SubprocessCaller()
    # SMTP password hash only works python < 3.4

    # create IAM group
    # aws iam create-group --group-name Admins
    print('\nCreating group %s:' % (group_name, ))
    create_group_command = "aws iam create-group --group-name %s" % (group_name,)
    command.set_command(create_group_command)
    output = command.execute()
    print(output)

    # add group policy to IAM group
    # aws iam put-group-policy --group-name {{ group_name }} --policy-document file:///home/clive/Code/aws/iam-policy-typhon-client-ses-notifiers.json --policy-name typhon-client-ses-notifier
    print('\nAdding policy %s to group %s:' % (policy_name, group_name))
    create_group_policy_command = "aws iam put-group-policy --group-name %s --policy-document %s --policy-name %s" % (group_name, policy_file, policy_name)
    command.set_command(create_group_policy_command)
    output = command.execute()
    print(output)

    # create user
    # aws iam create-user --user-name tc-clientname-ses-notifier
    # {
    #     "User": {
    #         "Path": "/",
    #         "UserName": "tc-clientname-ses-notifier",
    #         "UserId": "xxxxxxxx",
    #         "Arn": "arn:aws:iam::yyyyyyyy:user/tc-xxxxxxxxx-ses-notifier",
    #         "CreateDate": "2017-04-02T07:45:44.467Z"
    #     }
    # }
    print('\nCreating user %s' % (user_name, ))
    create_user_command = "aws iam create-user --user-name %s" % (user_name,)
    command.set_command(create_user_command)
    output = command.execute()
    print(output)

    # add user to group
    # aws iam add-user-to-group --group-name typhon-client-ses-notifiers --user-name tc-clientname-ses-notifier
    print('\nAdding user %s to group %s' % (user_name, group_name))
    create_user_command = "aws iam create-user --user-name %s" % (user_name,)
    command.set_command(create_user_command)
    output = command.execute()
    print(output)

    # create users access key
    # aws iam create-access-key --user-name tc-clientname-ses-notifier
    # {
    #     "AccessKey": {
    #         "UserName": "tc-clientname-ses-notifier-ses-notifier",
    #         "AccessKeyId": "xxxxxxxx",
    #         "Status": "Active",
    #         "SecretAccessKey": "xxxxxxx",
    #         "CreateDate": "2017-04-02T07:57:48.887Z"
    #     }
    # }
    print('\nCreating access key for user %s' % (user_name, ))
    create_user_command = "aws iam create-access-key --user-name %s" % (user_name,)
    command.set_command(create_user_command)
    output = command.execute()
    print(output)

    # convert SecretAccessKey to SMTP password
    # https://docs.aws.amazon.com/ses/latest/DeveloperGuide/smtp-credentials.html#smtp-credentials-convert
    print(
        """
        This program isnt finished. The rest is manual.

        To authentciate against the SES SMTP server, you need to convert the SecretAccessKey to an SMTP password by hashing it.

        Copy the AccessKey SecretAccessKey value from the above output and run the follwing:
        $ new_user = IAM_user()
        $ new_user.set_SecretAccessKey(SecretAccessKey)
        $ new_user.hash_SmtpPassword()
        $ print(new_user.SmtpPassword)

        """
    )
