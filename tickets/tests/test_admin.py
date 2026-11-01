from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tickets.models import Ticket, TicketStatus

CHANGELIST_URL = '/admin/tickets/ticket/'


class TicketAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username='responsavel',
            email='responsavel@example.com',
            password='senha-de-teste-123',
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_admin_search_by_client_and_subject(self):
        bakery = Ticket.objects.create(client='Padaria Bom Dia', subject='Atualizar cardápio do site')
        studio = Ticket.objects.create(client='Studio Lume', subject='Revisar contrato')

        response = self.client.get(CHANGELIST_URL, {'q': 'Padaria'})
        self.assertEqual(list(response.context['cl'].result_list), [bakery])

        response = self.client.get(CHANGELIST_URL, {'q': 'contrato'})
        self.assertEqual(list(response.context['cl'].result_list), [studio])

    def test_admin_filter_by_status(self):
        Ticket.objects.create(client='A', subject='Pendente')
        Ticket.objects.create(client='B', subject='Em andamento', status=TicketStatus.IN_PROGRESS)
        completed = Ticket.objects.create(client='C', subject='Concluído', status=TicketStatus.COMPLETED)

        response = self.client.get(CHANGELIST_URL, {'status__exact': 'completed'})

        self.assertEqual(list(response.context['cl'].result_list), [completed])

    def test_admin_save_applies_completion_rule(self):
        ticket = Ticket.objects.create(client='Padaria Bom Dia', subject='Atualizar cardápio do site')
        url = reverse('admin:tickets_ticket_change', args=[ticket.pk])

        response = self.client.post(url, {
            'client': ticket.client,
            'subject': ticket.subject,
            'description': '',
            'status': TicketStatus.COMPLETED,
            '_save': 'Salvar',
        })

        self.assertEqual(response.status_code, 302)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, TicketStatus.COMPLETED)
        self.assertIsNotNone(ticket.completed_at)
