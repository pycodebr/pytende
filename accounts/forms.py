from django import forms
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    """Login form with a single generic message for any invalid credentials."""

    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': 'Usuário ou senha inválidos.',
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields['username'].label = 'Usuário'
        self.fields['username'].widget.attrs['autocomplete'] = 'username'
        self.fields['password'].label = 'Senha'
        self.fields['password'].widget.attrs['autocomplete'] = 'current-password'
