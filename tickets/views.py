from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from tickets.forms import TicketCreateForm, TicketStatusForm, TicketUpdateForm
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
        context['status_choices'] = TicketStatus.choices
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


class TicketStatusUpdateView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def handle_no_permission(self):
        # Depois do login, voltar para esta rota (só POST) daria 405.
        return redirect_to_login(reverse('tickets:list'))

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        form = TicketStatusForm(request.POST)
        if form.is_valid():
            ticket.change_status(form.cleaned_data['status'])
            messages.success(
                request,
                f'Status de "{ticket.subject}" alterado para {ticket.get_status_display()}.',
            )
        else:
            messages.error(request, 'Status inválido. Nenhuma alteração foi feita.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        next_url = self.request.POST.get('next', '')
        if url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return reverse('tickets:list')
