#!/bin/sh

echo "Waiting for MySQL at $DB_HOST:$DB_PORT..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 0.1
done
echo "MySQL ready."

# run migrations
python manage.py migrate --noinput
python manage.py create_default_admin

# collect static — runs here where env vars are available
python manage.py collectstatic --noinput

echo "Starting server..."
exec "$@"