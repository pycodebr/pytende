from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from tickets.forms import TicketCreateForm, TicketUpdateForm
from tickets.models import Ticket, TicketStatus


class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'

    def get_current_status(self):
        status = self.request.GET.get('status', '')
        return status if status in TicketStatus.values else ''

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.get_current_status()
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_status = self.get_current_status()
        list_url = reverse('tickets:list')
        options = [('', 'Todos'), *TicketStatus.choices]
        context['current_status'] = current_status
        context['current_status_label'] = dict(TicketStatus.choices).get(current_status, '')
        context['status_filters'] = [
            {
                'value': value,
                'label': label,
                'url': f'{list_url}?status={value}' if value else list_url,
                'is_active': value == current_status,
            }
            for value, label in options
        ]
        return context


class TicketCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = TicketCreateForm
    template_name = 'tickets/ticket_form.html'
    success_url = reverse_lazy('tickets:list')
    success_message = 'Atendimento cadastrado com sucesso.'
    extra_context = {
        'page_title': 'Novo atendimento',
        'submit_label': 'Cadastrar atendimento',
    }


class TicketUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Ticket
    form_class = TicketUpdateForm
    template_name = 'tickets/ticket_form.html'
    success_url = reverse_lazy('tickets:list')
    success_message = 'Atendimento atualizado com sucesso.'
    extra_context = {
        'page_title': 'Editar atendimento',
        'submit_label': 'Salvar alterações',
    }

    def get_object(self, queryset=None):
        ticket = super().get_object(queryset)
        # Datas gravadas no banco. Num POST com erro, o form já aplicou na
        # instância os valores enviados; o bloco de datas mostra o que está salvo.
        self.saved_dates = {
            'created_at': ticket.created_at,
            'completed_at': ticket.completed_at,
        }
        return ticket

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['saved_dates'] = self.saved_dates
        return context
