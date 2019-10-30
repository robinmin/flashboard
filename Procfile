web: gunicorn wsgi:app --log-file -
worker: celery worker -A worker.celery --beat --loglevel=info
