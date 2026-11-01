from django.db import models
from django.utils import timezone

from base.models import BaseModel


class TicketStatus(models.TextChoices):
    PENDING = 'pending', 'Pendente'
    IN_PROGRESS = 'in_progress', 'Em andamento'
    COMPLETED = 'completed', 'Concluído'


class Ticket(BaseModel):
    client = models.CharField('cliente', max_length=150)
    subject = models.CharField('assunto', max_length=200)
    description = models.TextField('descrição', blank=True)
    status = models.CharField(
        'status',
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.PENDING,
    )
    completed_at = models.DateTimeField(
        'concluído em',
        null=True,
        blank=True,
        editable=False,
    )

    class Meta:
        verbose_name = 'atendimento'
        verbose_name_plural = 'atendimentos'
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['-created_at'], name='tickets_created_idx'),
            models.Index(fields=['status', '-created_at'], name='tickets_status_created_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=TicketStatus.values),
                name='tickets_status_valid',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status=TicketStatus.COMPLETED, completed_at__isnull=False)
                    | (~models.Q(status=TicketStatus.COMPLETED) & models.Q(completed_at__isnull=True))
                ),
                name='tickets_completed_at_matches_status',
            ),
        ]

    def __str__(self):
        return f'{self.client} - {self.subject}'

    def _sync_completed_at(self):
        if self.status == TicketStatus.COMPLETED:
            if self.completed_at is None:
                self.completed_at = timezone.now()
        else:
            self.completed_at = None

    def clean(self):
        super().clean()
        self._sync_completed_at()

    def save(self, *args, **kwargs):
        self._sync_completed_at()
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and 'status' in update_fields:
            kwargs['update_fields'] = {*update_fields, 'completed_at'}
        super().save(*args, **kwargs)

    def change_status(self, new_status):
        self.status = new_status
        self.save(update_fields=['status', 'updated_at'])
