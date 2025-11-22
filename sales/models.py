from django.db import models, transaction
from django.core.exceptions import ValidationError
from decimal import Decimal

# Herança do SoftDelete apenas para o Venda (Cabeçalho)

from base.models import SoftDeleteModel
from product.models import ProductVariation

class Sale(SoftDeleteModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Rascunho"  # Pode editar tudo
        COMPLETED = "COMPLETED", "Concluída"  # Bloqueada (Baixou estoque)
        CANCELED = "CANCELED", "Cancelada"  # Estornada (Devolveu estoque)

    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Data de Conclusão"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Status",
    )

    # Campos Desnormalizados (Totais)
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Venda #{self.pk} ({self.get_status_display()})"

    def calculate_totals(self):
        """Recalcula os totais baseados nos itens atuais."""
        # Se a venda já estiver concluída/cancelada, evitamos recalcular para garantir integridade histórica
        if self.status != self.Status.DRAFT:
            return

        total_items = self.items.aggregate(total=models.Sum("total_price"))[
            "total"
        ] or Decimal("0.00")

        self.gross_amount = total_items
        self.net_amount = total_items - self.discount_amount
        self.save(update_fields=["gross_amount", "net_amount"])

    @transaction.atomic
    def complete_sale(self):
        """
        MÉTODO CRÍTICO: Finaliza a venda.
        1. Valida estoque
        2. Baixa estoque
        3. Muda status
        """
        if self.status != self.Status.DRAFT:
            raise ValidationError("Apenas vendas em Rascunho podem ser concluídas.")

        if not self.items.exists():
            raise ValidationError("Não é possível concluir uma venda sem itens.")

        # Itera sobre os itens para baixar estoque
        for item in self.items.select_related("variation"):
            variation = item.variation

            # Validação de concorrência (Race Condition)
            # Bloqueia a linha do produto no banco até terminar a transação
            variation = ProductVariation.objects.select_for_update().get(
                pk=variation.pk
            )

            if variation.stock < item.quantity:
                raise ValidationError(
                    f"Estoque insuficiente para {variation}. Restante: {variation.stock}"
                )

            variation.stock -= item.quantity
            variation.save()

        from django.utils import timezone

        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    @transaction.atomic
    def cancel_sale(self):
        """
        Estorna a venda e devolve produtos ao estoque.
        """
        if self.status != self.Status.COMPLETED:
            raise ValidationError("Apenas vendas concluídas podem ser canceladas.")

        # Devolve estoque
        for item in self.items.select_related("variation"):
            variation = item.variation
            # Lock para segurança
            variation = ProductVariation.objects.select_for_update().get(
                pk=variation.pk
            )
            variation.stock += item.quantity
            variation.save()

        self.status = self.Status.CANCELED
        self.delete()  # Soft Delete da Venda


class SaleItem(models.Model):
    """
    SaleItem usa HARD DELETE.
    Motivo Profissional: Itens removidos de um rascunho são irrelevantes.
    A segurança vem do bloqueio de edição quando a Sale.status != DRAFT.
    """

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    variation = models.ForeignKey(
        ProductVariation, on_delete=models.PROTECT, related_name="sale_items"
    )

    # Snapshots (Imutabilidade de dados históricos)
    product_sku_snapshot = models.CharField(max_length=50, blank=True)
    product_name_snapshot = models.CharField(max_length=255, blank=True)

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Item da Venda"
        verbose_name_plural = "Itens da Venda"
        constraints = [
            # Constraint simples e eficiente
            models.UniqueConstraint(
                fields=["sale", "variation"], name="unique_variation_per_sale"
            )
        ]

    def clean(self):
        # PROIBIR EDIÇÃO SE NÃO FOR RASCUNHO
        # Isso garante a integridade fiscal sem precisar de Soft Delete aqui
        if self.sale_id and self.sale.status != Sale.Status.DRAFT:
            raise ValidationError(
                "Não é possível alterar itens de uma venda finalizada."
            )

    def save(self, *args, **kwargs):
        self.clean()  # Chama a validação acima

        # Lógica de Snapshot
        if not self.pk:  # Apenas na criação
            self.product_sku_snapshot = self.variation.sku
            self.product_name_snapshot = str(self.variation)

            if self.unit_price is None:
                self.unit_price = self.variation.product.selling_price

        # Cálculo Matemático
        bruto = self.unit_price * self.quantity
        self.total_price = max(bruto - self.discount, Decimal("0.00"))

        super().save(*args, **kwargs)

        # Atualiza o cabeçalho da venda
        self.sale.calculate_totals()

    def delete(self, *args, **kwargs):
        # PROIBIR EXCLUSÃO SE NÃO FOR RASCUNHO
        if self.sale.status != Sale.Status.DRAFT:
            raise ValidationError(
                "Não é possível remover itens de uma venda finalizada. Cancele a venda inteira."
            )

        super().delete(*args, **kwargs)

        # Atualiza o cabeçalho da venda após deletar
        self.sale.calculate_totals()
