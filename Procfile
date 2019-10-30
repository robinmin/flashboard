web: gunicorn wsgi:app --log-file -
worker: celery worker -A manage.celery --beat --loglevel=info
