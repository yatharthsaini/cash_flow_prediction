#!/bin/sh

#You have 20 unapplied migration(s). Your project may not work properly until you apply the migrations for app(s): admin, auth, cam, contenttypes, sessions.
#yes | python manage.py makemigrations
yes | python manage.py migrate
python manage.py collectstatic --noinput

if [ "$ENVIRONMENT" != "PRODUCTION" ]; then
  # Do something if the ENVIRONMENT variable is set to LOCAL
  echo "The ENVIRONMENT variable is set to LOCAL"
  python manage.py runserver 0.0.0.0:8000
else
  # Do something if the ENVIRONMENT variable is not set to LOCAL
  echo "The ENVIRONMENT variable is not set to LOCAL"
  gunicorn cash_flow_prediction.asgi --bind 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker --reload --timeout 300 --workers 5 --threads=100
fi
