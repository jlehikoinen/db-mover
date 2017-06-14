#!/usr/bin/env python
# -*- coding: utf-8 -*-

from hashlib import sha256
import hmac
import json
import os
import threading

from flask import abort, Flask, request
import db_mover
import config as cfg

"""
Notes

- Dropbox uid is now ignored in parsing response

"""

# API token for testing
APP_SECRET = os.environ['APP_SECRET']

# Flask app
app = Flask(__name__)
app.debug = True

# Flask secret
app.secret_key = os.environ['FLASK_SECRET_KEY']

# Flask functions
def validate_request():
    """Validate that the request is properly signed by Dropbox.
       (If not, this is a spoofed webhook.)
    """

    signature = request.headers.get('X-Dropbox-Signature')
    return signature == hmac.new(APP_SECRET, request.data, sha256).hexdigest()


@app.route('/')
def index():
    """Static index page"""

    message = 'DB WEBHOOK'
    return message


@app.route('/webhook', methods=['GET'])
def challenge():
    """Respond to the webhook challenge (GET request)
    by echoing back the challenge parameter.
    """

    # logger.info()
    return request.args.get('challenge')


@app.route('/webhook', methods=['POST'])
def webhook():
    """Validate request and run main script.
    """

    # Make sure this is a valid request from Dropbox
    if not validate_request():
        abort(403)

    db_mover.main()

    return ''


if __name__ == '__main__':
    app.run()
