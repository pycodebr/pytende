from django.contrib import admin

from tickets.models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('client', 'subject', 'status', 'created_at', 'completed_at')
    list_filter = ('status',)
    search_fields = ('client', 'subject')
    readonly_fields = ('completed_at', 'created_at', 'updated_at')
