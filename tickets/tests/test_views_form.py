from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase

from tickets.models import Ticket, TicketStatus


class LoggedInTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username='responsavel',
            email='responsavel@example.com',
            password='senha-de-teste-123',
        )

    def setUp(self):
        self.client.force_login(self.user)


class TicketCreateViewTests(LoggedInTestCase):
    url = '/tickets/new/'

    def test_create_page_renders(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="client"')
        self.assertContains(response, 'name="subject"')
        self.assertContains(response, 'name="description"')
        self.assertNotContains(response, 'name="status"')
        self.assertContains(response, '<title>Novo atendimento - Pytende</title>')
        self.assertContains(response, 'Todo atendimento novo começa como Pendente.')

    def test_create_valid_ticket_redirects_with_message(self):
        response = self.client.post(self.url, {
            'client': 'Padaria Bom Dia',
            'subject': 'Atualizar cardápio do site',
            'description': '',
        })

        self.assertRedirects(response, '/', fetch_redirect_response=False)
        ticket = Ticket.objects.get()
        self.assertEqual(ticket.client, 'Padaria Bom Dia')
        self.assertEqual(ticket.status, TicketStatus.PENDING)
        self.assertIsNone(ticket.completed_at)
        response = self.client.get('/')
        self.assertContains(response, 'Atendimento cadastrado com sucesso.')

    def test_create_ignores_posted_status(self):
        self.client.post(self.url, {
            'client': 'Padaria Bom Dia',
            'subject': 'Atualizar cardápio do site',
            'status': TicketStatus.COMPLETED,
        })

        ticket = Ticket.objects.get()
        self.assertEqual(ticket.status, TicketStatus.PENDING)
        self.assertIsNone(ticket.completed_at)

    def test_create_invalid_keeps_data_and_shows_errors(self):
        response = self.client.post(self.url, {
            'client': '   ',
            'subject': '',
            'description': 'Detalhes',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ticket.objects.exists())
        self.assertContains(response, 'Informe o cliente.')
        self.assertContains(response, 'Informe o assunto.')
        self.assertContains(response, 'aria-describedby="id_client_error"')
        self.assertContains(response, 'aria-describedby="id_subject_error"')
        self.assertContains(response, 'id="id_client_error"')
        self.assertContains(response, 'id="id_subject_error"')
        self.assertContains(response, 'aria-invalid="true"', count=2)
        self.assertContains(response, 'value="   "')
        self.assertContains(response, '>\nDetalhes</textarea>')
        self.assertEqual(list(get_messages(response.wsgi_request)), [])


COMPLETED_AT = datetime(2026, 11, 3, 17, 30, tzinfo=dt_timezone.utc)


class TicketUpdateViewTests(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        with patch('django.utils.timezone.now', return_value=datetime(2026, 11, 1, 15, 0, tzinfo=dt_timezone.utc)):
            self.ticket = Ticket.objects.create(
                client='Padaria Bom Dia',
                subject='Atualizar cardápio do site',
                description='Trocar os preços de novembro.',
            )
        self.url = f'/tickets/{self.ticket.pk}/edit/'

    def post_data(self, **overrides):
        data = {
            'client': self.ticket.client,
            'subject': self.ticket.subject,
            'description': self.ticket.description,
            'status': self.ticket.status,
        }
        data.update(overrides)
        return data

    def test_update_page_prefilled(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<title>Editar atendimento - Pytende</title>')
        self.assertContains(response, 'value="Padaria Bom Dia"')
        self.assertContains(response, 'value="Atualizar cardápio do site"')
        self.assertContains(response, 'Trocar os preços de novembro.</textarea>')
        self.assertContains(response, '<option value="pending" selected>Pendente</option>', html=True)
        self.assertContains(response, '<dt>Aberto em</dt><dd>01/11/2026 12:00</dd>', html=True)
        self.assertContains(response, '<dt>Concluído em</dt><dd>—</dd>', html=True)
        self.assertContains(response, 'Salvar alterações')

    def test_update_valid_redirects_with_message(self):
        response = self.client.post(self.url, self.post_data(subject='Assunto revisado'))

        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.subject, 'Assunto revisado')
        self.assertContains(self.client.get('/'), 'Atendimento atualizado com sucesso.')

    def test_update_to_completed_sets_completed_at(self):
        with patch('django.utils.timezone.now', return_value=COMPLETED_AT):
            response = self.client.post(self.url, self.post_data(status=TicketStatus.COMPLETED))

        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, TicketStatus.COMPLETED)
        self.assertEqual(self.ticket.completed_at, COMPLETED_AT)

    def test_update_reopen_clears_completed_at(self):
        self.ticket.change_status(TicketStatus.COMPLETED)

        response = self.client.post(self.url, self.post_data(status=TicketStatus.PENDING))

        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, TicketStatus.PENDING)
        self.assertIsNone(self.ticket.completed_at)

    def test_update_invalid_keeps_data_and_shows_errors(self):
        before = Ticket.objects.values().get(pk=self.ticket.pk)

        response = self.client.post(self.url, self.post_data(subject='', status=TicketStatus.IN_PROGRESS))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Ticket.objects.values().get(pk=self.ticket.pk), before)
        self.assertContains(response, 'Informe o assunto.')
        self.assertContains(response, 'aria-describedby="id_subject_error"')
        self.assertContains(response, '<option value="in_progress" selected>Em andamento</option>', html=True)

    def test_update_unknown_ticket_returns_404(self):
        self.assertEqual(self.client.get('/tickets/9999/edit/').status_code, 404)
