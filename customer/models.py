from django.db import models
from .validators import validate_cpf_cnpj


class Customer(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nome Completo")
    cpf_cnpj = models.CharField(
        max_length=18,
        unique=True,
        verbose_name="CPF/CNPJ",
        validators=[validate_cpf_cnpj],
        help_text="Informe CPF (11 dígitos) ou CNPJ (14 dígitos)"
    )
    birth_date = models.DateField(blank=True, null=True, verbose_name="Data de Nascimento")
    email = models.EmailField(unique=True, verbose_name="E-mail")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone/WhatsApp")
    baby_due_date = models.DateField(
        blank=True, null=True, verbose_name="Data Prevista do Parto"
    )
    size_preferences = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Preferências de Tamanho",
        help_text="Ex: P, M, G"
    )
    note = models.TextField(blank=True, null=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Cadastrado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_purchase_history(self):
        """
        Retorna o histórico de compras do cliente.
        TODO: Implementar quando o módulo de vendas/PDV estiver disponível.
        """
        # Placeholder: quando o modelo Sale existir, usar:
        # return self.sales.all().order_by('-sale_date')
        return []

    def get_total_spent(self):
        """
        Retorna o valor total gasto pelo cliente.
        TODO: Implementar quando o módulo de vendas/PDV estiver disponível.
        """
        # Placeholder: quando o modelo Sale existir, usar:
        # from django.db.models import Sum
        # return self.sales.aggregate(total=Sum('total_amount'))['total'] or 0
        return 0

    def get_purchase_frequency(self):
        """
        Retorna a frequência de compras (número de compras por mês).
        TODO: Implementar quando o módulo de vendas/PDV estiver disponível.
        """
        # Placeholder: quando o modelo Sale existir, calcular:
        # - Total de compras
        # - Período desde primeira compra
        # - Retornar média mensal
        return {
            'total_purchases': 0,
            'months_active': 0,
            'average_per_month': 0
        }

    def get_favorite_products(self, limit=5):
        """
        Retorna os produtos mais comprados pelo cliente.
        TODO: Implementar quando o módulo de vendas/PDV estiver disponível.
        """
        # Placeholder: quando o modelo SaleItem existir, usar:
        # from django.db.models import Count, Sum
        # return produtos mais frequentes nas vendas deste cliente
        return []


class Address(models.Model):
    cep = models.CharField(max_length=10, verbose_name="CEP")
    state = models.CharField(max_length=100, verbose_name="Estado")
    city = models.CharField(max_length=100, verbose_name="Cidade")
    neighborhood = models.CharField(max_length=100, verbose_name="Bairro")
    street = models.CharField(max_length=255, verbose_name="Rua")
    number = models.CharField(max_length=20, verbose_name="Número")
    complement = models.CharField(max_length=255, blank=True, null=True, verbose_name="Complemento")
    customer = models.ForeignKey(
        "Customer", on_delete=models.CASCADE, related_name="addresses", verbose_name="Cliente"
    )

    class Meta:
        verbose_name = "Endereço"
        verbose_name_plural = "Endereços"

    def __str__(self):
        return f"{self.street}, {self.number} - {self.neighborhood}, {self.city}/{self.state}"
