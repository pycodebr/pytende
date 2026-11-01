from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from tickets.models import Ticket


class TicketListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username='responsavel',
            email='responsavel@example.com',
            password='senha-de-teste-123',
        )

    def setUp(self):
        self.client.force_login(self.user)

    def create_at(self, moment, **kwargs):
        with patch('django.utils.timezone.now', return_value=moment):
            return Ticket.objects.create(**kwargs)

    def test_list_shows_columns_and_newest_first(self):
        oldest = self.create_at(
            datetime(2026, 11, 1, 12, 0, tzinfo=dt_timezone.utc),
            client='Padaria Bom Dia', subject='Atualizar cardápio do site',
        )
        middle = self.create_at(
            datetime(2026, 11, 2, 12, 0, tzinfo=dt_timezone.utc),
            client='Studio Lume', subject='Revisar logotipo',
        )
        newest = self.create_at(
            datetime(2026, 11, 3, 12, 0, tzinfo=dt_timezone.utc),
            client='Oficina Dois Irmãos', subject='Publicar página de orçamento',
        )

        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['tickets']), [newest, middle, oldest])
        html = response.content.decode()
        positions = [html.index(ticket.subject) for ticket in (newest, middle, oldest)]
        self.assertEqual(positions, sorted(positions))
        for header in ('Cliente', 'Assunto', 'Status', 'Aberto em', 'Concluído em'):
            self.assertContains(response, header)
        for ticket in (newest, middle, oldest):
            self.assertContains(response, ticket.client)
        self.assertContains(response, 'Pendente', count=3)
        self.assertContains(response, '01/11/2026 09:00')
        self.assertContains(response, '—', count=3)

    def test_list_dates_use_sao_paulo_timezone(self):
        self.create_at(
            datetime(2026, 11, 1, 15, 0, tzinfo=dt_timezone.utc),
            client='Padaria Bom Dia', subject='Atualizar cardápio do site',
        )

        response = self.client.get('/')

        self.assertContains(response, '01/11/2026 12:00')
