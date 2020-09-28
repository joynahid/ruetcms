import os, datetime

DEBUG = True

SECRET_KEY = os.urandom(24)
PERMANENT_SESSION_LIFETIME = datetime.timedelta(days = 10)

# Celery

CELERY_BROKER_URL='redis://localhost:6379'
CELERY_RESULT_BACKEND='redis://localhost:6379'

print("Configed")