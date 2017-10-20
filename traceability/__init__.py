"""
The Traceability Python library.
"""
__version__ = '1.1.5'
AUTHOR = "Piotr Wilkosz"
EMAIL = "Piotr.Wilkosz@gmail.com"
NAME = "HLTrace"

import logging
import tempfile
import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from .helpers import parse_config, parse_args

logger = logging.getLogger(__package__.ljust(12)[:12])

_opts, _args = parse_args()
_config = {}

# get SQL DBURI value from:
# 1. DATABASE_URL environment variable
# 2. cofniguration file = dburi section
# 3. Create HLTrace.sqlite file in tmp dir. 

try:
    _config['dburi'] = parse_config(_opts.config)['main']['dburi'][0]
except Exception as e:
    _config['dburi'] = 'sqlite:///' + tempfile.gettempdir() + os.sep + NAME + '.sqlite'
    
if 'DATABASE_URL' in os.environ: 
    _config['dburi'] = os.environ.get('DATABASE_URL')

_app = Flask(__name__)
_app.config['SQLALCHEMY_DATABASE_URI'] = _config['dburi']
db = SQLAlchemy(_app)

# try to create schema
db.create_all()
