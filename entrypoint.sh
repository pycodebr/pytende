#!/bin/sh
set -e

echo ">>> Aguardando o banco de dados..."
python manage.py wait_for_db --timeout 90

echo ">>> Aplicando migrations (advisory lock para mais de uma réplica)..."
python <<'PY'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute('SELECT pg_advisory_lock(1)')
    try:
        call_command('migrate', '--noinput')
    finally:
        cursor.execute('SELECT pg_advisory_unlock(1)')
PY

echo ">>> Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

exec "$@"
