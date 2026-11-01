from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.utils import OperationalError
from django.test import TestCase


class WaitForDbTests(TestCase):
    def test_wait_for_db_succeeds_and_times_out(self):
        out = StringIO()
        call_command('wait_for_db', timeout=1, stdout=out)
        self.assertIn('Banco de dados disponível.', out.getvalue())

        with patch(
            'django.db.backends.base.base.BaseDatabaseWrapper.ensure_connection',
            side_effect=OperationalError('connection refused'),
        ):
            with self.assertRaises(CommandError) as ctx:
                call_command('wait_for_db', timeout=1, stdout=StringIO())

        self.assertIn('Banco indisponível após 1s', str(ctx.exception))
