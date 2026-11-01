from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.test import TestCase

from tickets.models import Ticket, TicketStatus

COMPLETED_AT = datetime(2026, 11, 3, 17, 30, tzinfo=dt_timezone.utc)
LATER = datetime(2026, 11, 5, 10, 0, tzinfo=dt_timezone.utc)


def make_ticket(**kwargs):
    data = {'client': 'Padaria Bom Dia', 'subject': 'Atualizar cardápio do site'}
    data.update(kwargs)
    return Ticket.objects.create(**data)


class TicketModelTests(TestCase):
    def test_new_ticket_starts_pending(self):
        ticket = make_ticket()

        self.assertEqual(ticket.status, TicketStatus.PENDING)
        self.assertIsNone(ticket.completed_at)

    def test_status_choices(self):
        self.assertEqual(
            TicketStatus.choices,
            [
                ('pending', 'Pendente'),
                ('in_progress', 'Em andamento'),
                ('completed', 'Concluído'),
            ],
        )

    def test_completing_sets_completed_at(self):
        ticket = make_ticket()
        ticket.status = TicketStatus.COMPLETED
        with patch('django.utils.timezone.now', return_value=COMPLETED_AT):
            ticket.save()

        ticket.refresh_from_db()
        self.assertEqual(ticket.completed_at, COMPLETED_AT)

    def test_reopening_clears_completed_at(self):
        for new_status in (TicketStatus.PENDING, TicketStatus.IN_PROGRESS):
            with self.subTest(new_status=new_status):
                ticket = make_ticket(status=TicketStatus.COMPLETED)
                self.assertIsNotNone(ticket.completed_at)

                ticket.status = new_status
                ticket.save()

                ticket.refresh_from_db()
                self.assertIsNone(ticket.completed_at)

    def test_resaving_completed_ticket_keeps_completed_at(self):
        with patch('django.utils.timezone.now', return_value=COMPLETED_AT):
            ticket = make_ticket(status=TicketStatus.COMPLETED)

        ticket.description = 'Outra descrição'
        with patch('django.utils.timezone.now', return_value=LATER):
            ticket.full_clean()
            ticket.save()

        ticket.refresh_from_db()
        self.assertEqual(ticket.completed_at, COMPLETED_AT)

    def test_all_status_transitions_are_allowed(self):
        statuses = TicketStatus.values
        for origin in statuses:
            for target in statuses:
                if origin == target:
                    continue
                with self.subTest(origin=origin, target=target):
                    ticket = make_ticket(status=origin)
                    ticket.status = target
                    ticket.full_clean()
                    ticket.save()

                    ticket.refresh_from_db()
                    self.assertEqual(ticket.status, target)
                    if target == TicketStatus.COMPLETED:
                        self.assertIsNotNone(ticket.completed_at)
                    else:
                        self.assertIsNone(ticket.completed_at)

    def test_change_status_applies_completion_rule(self):
        ticket = make_ticket()
        updated_before = ticket.updated_at

        with patch('django.utils.timezone.now', return_value=COMPLETED_AT):
            ticket.change_status(TicketStatus.COMPLETED)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, TicketStatus.COMPLETED)
        self.assertEqual(ticket.completed_at, COMPLETED_AT)
        self.assertEqual(ticket.updated_at, COMPLETED_AT)
        self.assertNotEqual(ticket.updated_at, updated_before)

        with patch('django.utils.timezone.now', return_value=LATER):
            ticket.change_status(TicketStatus.IN_PROGRESS)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, TicketStatus.IN_PROGRESS)
        self.assertIsNone(ticket.completed_at)
        self.assertEqual(ticket.updated_at, LATER)

    def test_default_ordering_newest_first(self):
        older = datetime(2026, 11, 1, 12, 0, tzinfo=dt_timezone.utc)
        newer = datetime(2026, 11, 2, 12, 0, tzinfo=dt_timezone.utc)
        with patch('django.utils.timezone.now', return_value=older):
            first = make_ticket(subject='Primeiro')
        with patch('django.utils.timezone.now', return_value=newer):
            second = make_ticket(subject='Segundo')
            tie = make_ticket(subject='Empate')

        self.assertEqual(list(Ticket.objects.all()), [tie, second, first])

    def test_timestamps_are_managed(self):
        created = datetime(2026, 11, 1, 12, 0, tzinfo=dt_timezone.utc)
        with patch('django.utils.timezone.now', return_value=created):
            ticket = make_ticket()

        ticket.subject = 'Assunto revisado'
        with patch('django.utils.timezone.now', return_value=LATER):
            ticket.save()

        ticket.refresh_from_db()
        self.assertEqual(ticket.created_at, created)
        self.assertEqual(ticket.updated_at, LATER)

    def test_constraint_rejects_inconsistent_completed_at(self):
        ticket = make_ticket()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Ticket.objects.filter(pk=ticket.pk).update(status=TicketStatus.COMPLETED)

    def test_constraint_rejects_unknown_status(self):
        ticket = make_ticket()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Ticket.objects.filter(pk=ticket.pk).update(status='archived')

    def test_str(self):
        ticket = make_ticket()

        self.assertEqual(str(ticket), 'Padaria Bom Dia - Atualizar cardápio do site')
