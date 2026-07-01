from django.conf import settings
from django.db import models


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Destinatário',
    )
    customer = models.ForeignKey(
        'customer.Customer',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Cliente',
    )
    message = models.CharField(max_length=500, verbose_name='Mensagem')
    milestone_key = models.CharField(
        max_length=50,
        verbose_name='Marco',
        help_text="Ex: '30_weeks', 'post_partum'",
    )
    is_read = models.BooleanField(default=False, verbose_name='Lida')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criada em')

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']
        # Garante no banco que cada usuário recebe no máximo uma notificação
        # por marco por cliente — base da idempotência.
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'customer', 'milestone_key'],
                name='unique_notification_per_user_customer_milestone',
            )
        ]

    def __str__(self):
        return f"[{'✓' if self.is_read else '!'}] {self.user} — {self.customer} ({self.milestone_key})"
