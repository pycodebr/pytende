import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

PASSWORD = 'senha-de-teste-123'


class AuthTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username='responsavel',
            email='responsavel@example.com',
            password=PASSWORD,
        )

    def private_urls(self):
        return ['/']

    def test_superuser_created_by_command_can_log_in(self):
        self.user.delete()
        with patch.dict(os.environ, {'DJANGO_SUPERUSER_PASSWORD': PASSWORD}):
            call_command(
                'createsuperuser',
                interactive=False,
                username='responsavel',
                email='responsavel@example.com',
                verbosity=0,
            )

        user = get_user_model().objects.get(username='responsavel')
        self.assertIs(user.is_superuser, True)
        self.assertIs(user.is_staff, True)
        self.assertIs(self.client.login(username='responsavel', password=PASSWORD), True)

    def test_public_signup_routes_do_not_exist(self):
        for url in ('/register/', '/signup/', '/accounts/signup/'):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_login_page_renders_fields_in_portuguese(self):
        response = self.client.get('/login/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'Usuário')
        self.assertContains(response, 'Senha')
        self.assertContains(response, '<title>Entrar - Pytende</title>', html=False)

    def test_anonymous_user_is_redirected_to_login_with_next(self):
        expected = {
            '/?status=pending': '/login/?next=/%3Fstatus%3Dpending',
        }
        for url, redirect in expected.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, redirect, fetch_redirect_response=False)

    def test_login_redirects_to_next_url(self):
        response = self.client.post(
            '/login/?next=/%3Fstatus%3Dpending',
            {'username': 'responsavel', 'password': PASSWORD, 'next': '/?status=pending'},
        )

        self.assertRedirects(response, '/?status=pending', fetch_redirect_response=False)

    def test_login_without_next_redirects_to_ticket_list(self):
        response = self.client.post('/login/', {'username': 'responsavel', 'password': PASSWORD})

        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_login_ignores_external_next_url(self):
        response = self.client.post(
            '/login/',
            {
                'username': 'responsavel',
                'password': PASSWORD,
                'next': 'https://exemplo-externo.com/',
            },
        )

        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_invalid_credentials_show_generic_error(self):
        attempts = [
            {'username': 'responsavel', 'password': 'senha-errada'},
            {'username': 'nao-existe', 'password': PASSWORD},
        ]
        for data in attempts:
            with self.subTest(username=data['username']):
                response = self.client.post('/login/', data)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Usuário ou senha inválidos.', count=1)
                self.assertNotContains(response, 'senha incorreta')
                self.assertNotContains(response, 'usuário não existe')
                self.assertContains(response, f'value="{data["username"]}"')

    def test_logout_requires_post(self):
        self.client.force_login(self.user)

        response = self.client.get('/logout/')

        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_logout_form_present_on_private_screens(self):
        self.client.force_login(self.user)
        for url in self.private_urls():
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<form method="post" action="/logout/">')
                self.assertContains(response, 'csrfmiddlewaretoken')
                self.assertContains(response, 'Sair')

    def test_logout_ends_session(self):
        self.client.force_login(self.user)

        response = self.client.post('/logout/')

        self.assertRedirects(response, '/login/', fetch_redirect_response=False)
        self.assertRedirects(self.client.get('/'), '/login/?next=/', fetch_redirect_response=False)
