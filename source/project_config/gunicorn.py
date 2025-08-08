"""Gunicorn config file"""

# Django WSGI application path in pattern MODULE_NAME:VARIABLE_NAME
wsgi_app = "project_config.wsgi:application"
# restart workers after 90s of no activity (e.g. waiting for an API response)
timeout = 90
# The granularity of Error log outputs
loglevel = "info"
# send access logs to stdout
accesslog = "-"
# send error logs to stderr
errorlog = "-"
# The number of worker processes for handling requests
workers = 2
# The socket to bind
bind = "0.0.0.0:8000"
# Do not restart workers when code changes (production only!)
reload = False
# Do not start gunicorn in the background, otherwise, the  docker container exits immediately
daemon = False