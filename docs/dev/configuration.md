# Configuration

Configuration settings live in `/var/lib/medusa/medusa-xxx.ini` where `xxx` denotes the instance type, eg `development` or `production`, `branch-yyy-testing`.

To maintain consistency across instances, the origin of these config files are in an S3 bucket, `medusa-sebbqld`. The systemd config of `medusa` requires a service, `medusa-config` before starting. 

The `medusa-config` services simply executes `download_config.py` which uses `boto3` to copy the config files from S3 to `/var/lib/medusa/`.
