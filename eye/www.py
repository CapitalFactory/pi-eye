import os
import redis

import bottle
from bottle import mako_view as view

import logging
logger = logging.getLogger(__name__)

# tell bottle where to look for templates
import eye
bottle.TEMPLATE_PATH.append(os.path.join(eye.root, 'templates'))

redis_client = redis.StrictRedis()

# primary export
app = bottle.Bottle()

@app.get('/')
def root():
    bottle.redirect('/dashboard')

@app.get('/dashboard')
@view('dashboard.mako')
def index():
    # the worker should have populated the redis store
    return dict()
