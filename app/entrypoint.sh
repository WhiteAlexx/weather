#!/bin/sh

if [ "$POSTGRES_DB" = "weather" ]
then
    echo "Ждем postgres..."

    while ! nc -z "db_weather" $POSTGRES_PORT; do
      sleep 0.5
    done

    echo "PostgreSQL запущен"
fi

python manage.py makemigrations
python manage.py migrate

echo "Устанавливаем суперпользователя в БД default..."
python manage.py shell <<EOF
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv('DJANGO_SUPERUSER_USERNAME')
email = os.getenv('DJANGO_SUPERUSER_EMAIL')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print("Суперпользователь установлен в БД default")
else:
    print("Суперпользователь уже есть в БД default")
EOF

exec "$@"