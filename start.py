#!/usr/bin/env python

from flask_site import app
from flask_site.helpers.app_helper import flask_config


app.run(host=flask_config.get('bind_ip'), port=flask_config.get('bind_port'))
