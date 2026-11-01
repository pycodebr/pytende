from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from tickets.models import Ticket, TicketStatus


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
        self.assertContains(response, '<span class="badge badge--pending">Pendente</span>', count=3)
        self.assertContains(response, '01/11/2026 09:00')
        self.assertContains(response, '—', count=3)

    def test_list_dates_use_sao_paulo_timezone(self):
        self.create_at(
            datetime(2026, 11, 1, 15, 0, tzinfo=dt_timezone.utc),
            client='Padaria Bom Dia', subject='Atualizar cardápio do site',
        )

        response = self.client.get('/')

        self.assertContains(response, '01/11/2026 12:00')

    def create_one_of_each_status(self):
        return {
            status: Ticket.objects.create(
                client=f'Cliente {label}', subject=f'Assunto {label}', status=status,
            )
            for status, label in TicketStatus.choices
        }

    def test_list_filters_by_status_query_string(self):
        tickets = self.create_one_of_each_status()

        for status, ticket in tickets.items():
            with self.subTest(status=status):
                for _ in range(2):
                    response = self.client.get('/', {'status': status})
                    self.assertEqual(list(response.context['tickets']), [ticket])
                    self.assertEqual(response.context['current_status'], status)

    def test_list_without_or_with_invalid_filter_shows_all(self):
        tickets = self.create_one_of_each_status()

        for query in ({}, {'status': 'xyz'}):
            with self.subTest(query=query):
                response = self.client.get('/', query)
                self.assertEqual(set(response.context['tickets']), set(tickets.values()))
                self.assertEqual(response.context['current_status'], '')
                self.assertContains(response, '<a class="filter" href="/" aria-current="page">Todos</a>', html=True)
                self.assertContains(response, 'aria-current="page"', count=1)

    def test_list_marks_active_filter(self):
        response = self.client.get('/?status=completed')

        self.assertContains(response, 'aria-current="page"', count=1)
        self.assertContains(
            response,
            '<a class="filter" href="/?status=completed" aria-current="page">Concluído</a>',
            html=True,
        )
        for value, label in (('', 'Todos'), ('pending', 'Pendente'), ('in_progress', 'Em andamento')):
            href = f'/?status={value}' if value else '/'
            self.assertContains(response, f'<a class="filter" href="{href}">{label}</a>', html=True)

    def test_list_empty_state_with_create_link(self):
        Ticket.objects.create(client='Padaria Bom Dia', subject='Atualizar cardápio do site')

        response = self.client.get('/?status=completed')
        self.assertContains(response, 'Nenhum atendimento com status "Concluído".')
        self.assertContains(response, '<a class="btn btn--primary" href="/tickets/new/">Cadastrar atendimento</a>', html=True)

        Ticket.objects.all().delete()
        response = self.client.get('/')
        self.assertContains(response, 'Você ainda não tem atendimentos cadastrados.')
        self.assertContains(response, '<a class="btn btn--primary" href="/tickets/new/">Cadastrar atendimento</a>', html=True)

    def test_completed_filter_shows_completed_at(self):
        with patch('django.utils.timezone.now', return_value=datetime(2026, 11, 3, 17, 30, tzinfo=dt_timezone.utc)):
            Ticket.objects.create(client='Padaria Bom Dia', subject='Atualizar cardápio do site', status=TicketStatus.COMPLETED)

        response = self.client.get('/?status=completed')

        self.assertContains(response, 'Atualizar cardápio do site')
        self.assertContains(response, '03/11/2026 14:30')

    def test_screens_have_no_delete_action(self):
        ticket = Ticket.objects.create(client='Padaria Bom Dia', subject='Atualizar cardápio do site')

        for url in self.screens_without_delete(ticket):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'Excluir')
                self.assertNotContains(response, 'delete')

    def screens_without_delete(self, ticket):
        return ['/', f'/tickets/{ticket.pk}/edit/']
