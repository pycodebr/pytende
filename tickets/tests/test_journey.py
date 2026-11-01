import os
from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from tickets.models import Ticket, TicketStatus

PASSWORD = 'senha-de-teste-123'
COMPLETED_AT = datetime(2026, 11, 3, 17, 30, tzinfo=dt_timezone.utc)


class MainJourneyTests(TestCase):
    def test_main_journey(self):
        with patch.dict(os.environ, {'DJANGO_SUPERUSER_PASSWORD': PASSWORD}):
            call_command(
                'createsuperuser',
                interactive=False,
                username='responsavel',
                email='responsavel@example.com',
                verbosity=0,
            )
        menu = Ticket.objects.create(client='Padaria Bom Dia', subject='Atualizar cardápio do site')
        logo = Ticket.objects.create(client='Studio Lume', subject='Revisar logotipo')

        # Sem login, a lista de pendentes leva ao login guardando o caminho.
        response = self.client.get('/?status=pending')
        self.assertRedirects(response, '/login/?next=/%3Fstatus%3Dpending', fetch_redirect_response=False)
        self.assertEqual(self.client.get(response['Location']).status_code, 200)

        # O login volta para a lista de pendentes.
        response = self.client.post(
            '/login/?next=/%3Fstatus%3Dpending',
            {'username': 'responsavel', 'password': PASSWORD, 'next': '/?status=pending'},
        )
        self.assertRedirects(response, '/?status=pending', fetch_redirect_response=False)
        response = self.client.get('/?status=pending')
        self.assertEqual(list(response.context['tickets']), [logo, menu])

        # Troca para "em andamento" pela lista.
        response = self.client.post(
            f'/tickets/{menu.pk}/status/',
            {'status': TicketStatus.IN_PROGRESS, 'next': '/?status=pending'},
        )
        self.assertRedirects(response, '/?status=pending', fetch_redirect_response=False)
        response = self.client.get('/?status=pending')
        self.assertEqual(list(response.context['tickets']), [logo])
        self.assertContains(response, 'alterado para Em andamento.')
        response = self.client.get('/?status=in_progress')
        self.assertEqual(list(response.context['tickets']), [menu])

        # Conclui pela lista.
        with patch('django.utils.timezone.now', return_value=COMPLETED_AT):
            response = self.client.post(
                f'/tickets/{menu.pk}/status/',
                {'status': TicketStatus.COMPLETED, 'next': '/?status=in_progress'},
            )
        self.assertRedirects(response, '/?status=in_progress', fetch_redirect_response=False)

        # O filtro "Concluído" mostra só esse atendimento, com a data em São Paulo.
        response = self.client.get('/?status=completed')
        self.assertEqual(list(response.context['tickets']), [menu])
        self.assertContains(response, 'Atualizar cardápio do site')
        self.assertNotContains(response, 'Revisar logotipo')
        self.assertContains(response, '03/11/2026 14:30')
