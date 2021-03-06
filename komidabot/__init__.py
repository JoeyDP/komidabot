import os

from flask_sqlalchemy import SQLAlchemy
from flask import Flask

import redis


DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///menu.db')
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = VERIFY_TOKEN

db = SQLAlchemy(app)

redis_url = os.getenv('REDIS_URL')
redisCon = redis.from_url(redis_url)
