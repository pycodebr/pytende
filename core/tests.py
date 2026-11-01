from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase


class SettingsTests(TestCase):
    def test_locale_and_timezone_settings(self):
        self.assertEqual(settings.LANGUAGE_CODE, 'pt-br')
        self.assertEqual(settings.TIME_ZONE, 'America/Sao_Paulo')
        self.assertIs(settings.USE_TZ, True)
        self.assertIs(settings.USE_I18N, True)
        self.assertEqual(
            settings.DATABASES['default']['ENGINE'],
            'django.db.backends.postgresql',
        )


class EnvExampleTests(SimpleTestCase):
    EXPECTED_KEYS = [
        'SECRET_KEY',
        'DEBUG',
        'ALLOWED_HOSTS',
        'CSRF_TRUSTED_ORIGINS',
        'POSTGRES_DB',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'DATABASE_URL',
        'SECURE_SSL_REDIRECT',
        'SECURE_HSTS_SECONDS',
        'DOMAIN',
        'ACME_EMAIL',
        'TRAEFIK_DASHBOARD_AUTH',
    ]

    def read_env_example(self):
        path = Path(settings.BASE_DIR) / '.env.example'
        self.assertTrue(path.is_file(), '.env.example não existe na raiz do projeto.')
        values = {}
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, _, value = line.partition('=')
            values[key.strip()] = value.strip()
        return values

    def test_env_example_contains_only_placeholders(self):
        values = self.read_env_example()

        self.assertEqual(list(values), self.EXPECTED_KEYS)
        self.assertEqual(values['SECRET_KEY'], 'troque-por-uma-chave-gerada')
        self.assertEqual(values['POSTGRES_PASSWORD'], 'troque-esta-senha')
        self.assertEqual(values['TRAEFIK_DASHBOARD_AUTH'], '')
        self.assertTrue(values['DOMAIN'].endswith('example.com'))
        for key, value in values.items():
            with self.subTest(key=key):
                self.assertFalse(value.startswith('django-insecure-'))

        dockerignore = Path(settings.BASE_DIR) / '.dockerignore'
        self.assertTrue(dockerignore.is_file(), '.dockerignore não existe.')
        self.assertIn(
            '.env',
            [line.strip() for line in dockerignore.read_text(encoding='utf-8').splitlines()],
        )


class HealthCheckTests(TestCase):
    def test_health_returns_ok_without_queries(self):
        with self.assertNumQueries(0):
            response = self.client.get('/health/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})
