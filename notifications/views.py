from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from .models import Notification


class MarkNotificationReadView(LoginRequiredMixin, View):
    """Marca uma notificação como lida e retorna para a página anterior."""

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return redirect(request.META.get('HTTP_REFERER') or 'base:home')


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    """Marca todas as notificações não lidas do usuário como lidas."""

    def post(self, request):
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return redirect(request.META.get('HTTP_REFERER') or 'base:home')


class AlertasView(LoginRequiredMixin, ListView):
    """Lista todas as notificações dos últimos 7 dias (lidas e não lidas)."""

    template_name = 'notifications/alertas.html'
    context_object_name = 'notifications'
    paginate_by = 30

    def get_queryset(self):
        since = timezone.now() - timedelta(days=7)
        return (
            self.request.user.notifications
            .filter(created_at__gte=since)
            .select_related('customer')
            .order_by('-created_at')
        )
