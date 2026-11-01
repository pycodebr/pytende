import time

from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Waits until the default database accepts connections.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=60,
            help='Maximum number of seconds to wait (default: 60).',
        )

    def handle(self, *args, **options):
        timeout = options['timeout']
        deadline = time.monotonic() + timeout

        while True:
            try:
                connections['default'].ensure_connection()
            except OperationalError as exc:
                if time.monotonic() >= deadline:
                    raise CommandError(
                        f'Banco indisponível após {timeout}s: {exc}'
                    )
                self.stdout.write('Aguardando o banco de dados...')
                time.sleep(1)
            else:
                self.stdout.write(self.style.SUCCESS('Banco de dados disponível.'))
                return
