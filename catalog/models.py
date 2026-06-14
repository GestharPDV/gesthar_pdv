from django.db import models


class CatalogConfig(models.Model):
    whatsapp_number = models.CharField(
        max_length=20,
        verbose_name="Número WhatsApp",
        help_text="Formato: 5511999999999 (código país + DDD + número)",
    )
    instagram_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="URL Instagram",
        help_text="Ex: https://instagram.com/suaconta",
    )
    catalog_visible = models.BooleanField(default=True, verbose_name="Catálogo Visível")
    company_name = models.CharField(max_length=255, verbose_name="Nome da Empresa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Configuração do Catálogo"
        verbose_name_plural = "Configurações do Catálogo"

    def __str__(self):
        return f"Config: {self.company_name}"
