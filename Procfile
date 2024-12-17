release: python manage.py migrate
web: newrelic-admin run-program gunicorn clinks.wsgi --log-file -
worker: celery -A clinks worker --loglevel=info --concurrency=2
scheduler: celery -A clinks beat --loglevel=info