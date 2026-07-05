from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group

_MILESTONE_CACHE_KEY = 'last_milestone_check'
_MILESTONE_CACHE_TTL = 86400  # 24 horas


def _get_client_ip(request):
    """Retorna o IP real do cliente, considerando proxies."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or None


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Registra o login do usuário nos logs de atividade."""
    from .models import UserActionLog
    ip = _get_client_ip(request)
    UserActionLog.objects.create(
        user=user,
        action='Realizou login no sistema',
        action_type=UserActionLog.ActionType.LOGIN,
        ip_address=ip,
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Registra o logout do usuário nos logs de atividade."""
    if user is None:
        return
    from .models import UserActionLog
    ip = _get_client_ip(request)
    UserActionLog.objects.create(
        user=user,
        action='Realizou logout do sistema',
        action_type=UserActionLog.ActionType.LOGOUT,
        ip_address=ip,
    )


@receiver(user_logged_in)
def check_milestones_on_login(sender, request, user, **kwargs):
    """
    Dispara a verificação de marcos gestacionais uma vez por dia.
    O cache evita execuções redundantes quando múltiplos usuários
    fazem login no mesmo dia.
    """
    if not cache.get(_MILESTONE_CACHE_KEY):
        try:
            from notifications.services import run_milestone_check
            run_milestone_check()
        except Exception:
            pass  # Nunca deve bloquear o login
        cache.set(_MILESTONE_CACHE_KEY, True, timeout=_MILESTONE_CACHE_TTL)


@receiver(post_save, sender='user.UserGesthar')
def assign_user_group(sender, instance, **kwargs):
    """
    Mantém o grupo Django e o flag is_staff sincronizados com o campo `role`.
    Superusuários são ignorados para não interferir nas permissões do admin.
    """
    if instance.is_superuser:
        # Superusuários são sempre ADMIN — corrige caso o role esteja errado
        if instance.role != 'ADMIN':
            sender.objects.filter(pk=instance.pk).update(role='ADMIN')
        return

    is_admin = instance.role == 'ADMIN'
    group_name = 'Administrador' if is_admin else 'Vendedor'

    group, _ = Group.objects.get_or_create(name=group_name)
    instance.groups.set([group])

    # Atualiza is_staff sem disparar o signal novamente
    if instance.is_staff != is_admin:
        sender.objects.filter(pk=instance.pk).update(is_staff=is_admin)
