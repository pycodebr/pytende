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
