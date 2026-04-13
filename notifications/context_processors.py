from datetime import timedelta
from django.utils import timezone


def notifications(request):
    """
    Injeta contagem de não lidas e lista da última semana em todos os templates.
    Retorna valores vazios para usuários não autenticados.
    """
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'recent_notifications': [],
            'weekly_notifications': [],
        }

    unread_qs = (
        request.user.notifications
        .filter(is_read=False)
        .select_related('customer')
    )

    since = timezone.now() - timedelta(days=7)
    weekly_qs = (
        request.user.notifications
        .filter(created_at__gte=since)
        .select_related('customer')
        .order_by('-created_at')
    )

    return {
        'unread_notifications_count': unread_qs.count(),
        'recent_notifications': unread_qs.order_by('-created_at')[:5],
        'weekly_notifications': weekly_qs,
    }
