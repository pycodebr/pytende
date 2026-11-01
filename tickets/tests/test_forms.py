from django.test import TestCase

from tickets.forms import TicketCreateForm, TicketUpdateForm


class TicketFormTests(TestCase):
    def test_create_form_requires_client_and_subject(self):
        form = TicketCreateForm(data={'client': '', 'subject': '', 'description': ''})

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['client'], ['Informe o cliente.'])
        self.assertEqual(form.errors['subject'], ['Informe o assunto.'])

    def test_create_form_description_is_optional(self):
        form = TicketCreateForm(data={
            'client': 'Padaria Bom Dia',
            'subject': 'Atualizar cardápio do site',
            'description': '',
        })

        self.assertTrue(form.is_valid(), form.errors)

    def test_create_form_rejects_blank_spaces(self):
        form = TicketCreateForm(data={'client': '   ', 'subject': '   ', 'description': ''})

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['client'], ['Informe o cliente.'])
        self.assertEqual(form.errors['subject'], ['Informe o assunto.'])

    def test_create_form_has_no_status_field(self):
        self.assertNotIn('status', TicketCreateForm().fields)

    def test_fields_respect_max_length(self):
        cases = {
            'client': {'client': 'a' * 151, 'subject': 'Assunto'},
            'subject': {'client': 'Cliente', 'subject': 'a' * 201},
        }
        for field_name, data in cases.items():
            with self.subTest(field=field_name):
                form = TicketCreateForm(data=data)

                self.assertFalse(form.is_valid())
                self.assertIn(field_name, form.errors)
                self.assertEqual(len(form.errors), 1)

        valid = TicketCreateForm(data={'client': 'a' * 150, 'subject': 'a' * 200})
        self.assertTrue(valid.is_valid(), valid.errors)

    def test_update_form_fields_and_status_choices(self):
        form = TicketUpdateForm()
        self.assertEqual(list(form.fields), ['client', 'subject', 'description', 'status'])
        self.assertEqual(form.fields['status'].label, 'Status')

        invalid = TicketUpdateForm(data={'client': 'Cliente', 'subject': 'Assunto', 'status': 'archived'})
        self.assertFalse(invalid.is_valid())
        self.assertIn('status', invalid.errors)

        for status in ('pending', 'in_progress', 'completed'):
            with self.subTest(status=status):
                valid = TicketUpdateForm(data={'client': 'Cliente', 'subject': 'Assunto', 'status': status})
                self.assertTrue(valid.is_valid(), valid.errors)
