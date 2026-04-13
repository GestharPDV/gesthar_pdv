from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group


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
