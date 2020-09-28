import os, datetime

DEBUG = True

SECRET_KEY = os.environ['APP_SECRET']
PERMANENT_SESSION_LIFETIME = datetime.timedelta(days = 10)