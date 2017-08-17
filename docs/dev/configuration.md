# Configuration

The medusa app config is loaded in the following workflow:

- To maintain consistency across instances, the origin of the master config files is an S3 bucket, `medusa-sebbqld`.
- The `medusa` service (`/etc/systemd/system/medusa.service`) is enabled to start on boot.
- The `medusa` services requires the service, `medusa-config` (`/etc/systemd/system/medusa-config.service`), before starting.
- The `medusa-config` service simply executes `download_config.py` which uses `boto3` to copy the config files from S3 to `/var/lib/medusa/`.
- The `medusa` service loads `/var/lib/medusa/medusa-xxx.ini` into the ENVIRONMENT, where `xxx` denotes the instance type, eg `development` or `production`, `branch-yyy-testing`.
- The `medusa` Flask app loads the ENVIRONMENT into its config in `/var/www/medusa/app/__init__.py`.
