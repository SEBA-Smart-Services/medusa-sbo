# Asynchronus through Celery

Medusa uses a combination of [Flask-Celery](http://flask.pocoo.org/docs/0.12/patterns/celery/), [RabbitMQ](http://www.rabbitmq.com/) and [Redis](https://redis.io/) to create asynchronus tasks. These task are run in the same EC2 instance currently but can be expanded to a seperate server or instance at a later date. The files are currently saved to a temporary folder in reports however this needs to be changed to backend usage to make expansion easier.

Medusa uses two brokers RabbitMQ, which is used to handle the data, and Redis, which is used to get status updates from the worker. The broker is needed to queue tasks to give to the celery workers.

## Celery

The Celery module is quite easy to use once the configuration files have been set up and the brokers are running

The Celery task has been set up as a [daemon](http://docs.celeryproject.org/en/latest/userguide/daemonizing.html) to run in the background, currently if the server is stopped or reset for any purpose then the celery daemon needs to be restarted. This can be done by running the following command ***/etc/init.d/celeryd start***, in addition if any changes are made to the celery task then it will need to be restarted.

The configuration file can be found in ***/etc/default/celeryd***

To run the worker seperately (in the case of the dev server as the celery worker hasn't been set up to run as a daemon) you need to activate the virtual environment (*source env/bin/activate*) then export the Medusa settings and then run a command similar to the following: ***celery worker -A app.celery -l debug -Ofair***

## RabbitMQ

## Redis
