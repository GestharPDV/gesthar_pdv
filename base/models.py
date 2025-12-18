from django.db import models
from django.utils import timezone

class SoftDeleteQuerySet(models.QuerySet):
    def only_active(self):
        return self.filter(is_active=True)

    def only_deleted(self):
        return self.filter(is_active=False)

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        # Por padrão, esconde os deletados
        return SoftDeleteQuerySet(self.model, using=self._db).only_active()

class GlobalManager(models.Manager):
    def get_queryset(self):
        # Manager para quando precisarmos ver TUDO (inclusive deletados)
        # Ex: Para auditoria ou painel administrativo
        return SoftDeleteQuerySet(self.model, using=self._db)

class SoftDeleteModel(models.Model):
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Data de Exclusão")

    # Manager Padrão (Sales.objects.all() traz só os ativos)
    objects = SoftDeleteManager() 
    # Manager Global (Sales.all_objects.all() traz tudo)
    all_objects = GlobalManager()

    class Meta:
        abstract = True  # Não cria tabela no banco, serve de molde

    def delete(self, using=None, keep_parents=False):
        """
        Sobrescreve o método delete nativo.
        Ao invés de apagar do banco, marca como inativo.
        """
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(using=using)

    def hard_delete(self):
        """
        Método para apagar de verdade do banco (apenas para limpeza técnica/LGPD)
        """
        super().delete()