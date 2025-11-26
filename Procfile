release: python manage.py collectstatic --noinput && python manage.py migrate
web: gunicorn sales_project.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --workers 2
