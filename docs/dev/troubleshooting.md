# Debugging & troubleshooting

## Logging
- The `medusa` Flask app writes logs to `/var/log/uwsgi/medusa.log`.
- `nginx` writes logs to `/var/log/nginx/access.log` and `/var/log/nginx/error.log`.

## Bugsnag
Bugs and erros on any production servers are moinotred using [Bugsnag](https://www.bugsnag.com/). Bugsnag is integrated with the team [Slack](https://slack.com/) account for real time Slack notifications on bugs.

TODO: describe Bugsnag instantiation in app config.
