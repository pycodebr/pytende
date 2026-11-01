from django import forms

from tickets.models import Ticket, TicketStatus


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['client', 'subject', 'description']
        labels = {
            'client': 'Cliente',
            'subject': 'Assunto',
            'description': 'Descrição (opcional)',
        }
        error_messages = {
            'client': {'required': 'Informe o cliente.'},
            'subject': {'required': 'Informe o assunto.'},
        }
        widgets = {
            'client': forms.TextInput(attrs={'placeholder': 'Nome da pessoa ou da empresa'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class TicketUpdateForm(TicketCreateForm):
    class Meta(TicketCreateForm.Meta):
        fields = ['client', 'subject', 'description', 'status']
        labels = {**TicketCreateForm.Meta.labels, 'status': 'Status'}
        widgets = {**TicketCreateForm.Meta.widgets, 'status': forms.Select}


class TicketStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=TicketStatus.choices,
        error_messages={
            'required': 'Status inválido.',
            'invalid_choice': 'Status inválido.',
        },
    )
