web: bash -lc "python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py createsuperuser --noinput || true && gunicorn project.wsgi:application --bind 0.0.0.0:$PORT --workers 3"
worker: celery -A project worker -l info

