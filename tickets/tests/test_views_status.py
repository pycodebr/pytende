from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client, TestCase

from tickets.models import Ticket, TicketStatus

COMPLETED_AT = datetime(2026, 11, 3, 17, 30, tzinfo=dt_timezone.utc)


class TicketStatusUpdateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username='responsavel',
            email='responsavel@example.com',
            password='senha-de-teste-123',
        )

    def setUp(self):
        self.client.force_login(self.user)
        self.ticket = Ticket.objects.create(client='Padaria Bom Dia', subject='Atualizar cardápio do site')
        self.url = f'/tickets/{self.ticket.pk}/status/'

    def message_texts(self, response):
        return [str(message) for message in get_messages(response.wsgi_request)]

    def test_status_change_updates_and_redirects_to_next(self):
        response = self.client.post(self.url, {'status': 'in_progress', 'next': '/?status=pending'})

        self.assertRedirects(response, '/?status=pending', fetch_redirect_response=False)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, TicketStatus.IN_PROGRESS)
        self.assertEqual(
            self.message_texts(response),
            ['Status de "Atualizar cardápio do site" alterado para Em andamento.'],
        )
        page = self.client.get('/?status=pending')
        self.assertContains(page, 'Status de &quot;Atualizar cardápio do site&quot; alterado para Em andamento.')

    def test_status_change_rejects_get(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_status_change_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)

        response = csrf_client.post(self.url, {'status': 'completed'})

        self.assertEqual(response.status_code, 403)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, TicketStatus.PENDING)

    def test_status_change_to_completed_sets_date_and_reopen_clears(self):
        self.ticket.change_status(TicketStatus.IN_PROGRESS)

        with patch('django.utils.timezone.now', return_value=COMPLETED_AT):
            self.client.post(self.url, {'status': 'completed'})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.completed_at, COMPLETED_AT)

        self.client.post(self.url, {'status': 'in_progress'})
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.completed_at)

    def test_status_change_invalid_value_keeps_status(self):
        response = self.client.post(self.url, {'status': 'archived'})

        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, TicketStatus.PENDING)
        self.assertEqual(self.message_texts(response), ['Status inválido. Nenhuma alteração foi feita.'])
        self.assertContains(self.client.get('/'), 'Status inválido. Nenhuma alteração foi feita.')

    def test_status_change_ignores_external_next(self):
        response = self.client.post(self.url, {'status': 'in_progress', 'next': 'https://exemplo-externo.com/'})

        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_status_change_unknown_ticket_returns_404(self):
        response = self.client.post('/tickets/9999/status/', {'status': 'completed'})

        self.assertEqual(response.status_code, 404)
