from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from tickets.forms import TicketCreateForm
from tickets.models import Ticket


class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'


class TicketCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = TicketCreateForm
    template_name = 'tickets/ticket_form.html'
    success_url = reverse_lazy('tickets:list')
    success_message = 'Atendimento cadastrado com sucesso.'
    extra_context = {
        'page_title': 'Novo atendimento',
        'submit_label': 'Cadastrar atendimento',
    }
