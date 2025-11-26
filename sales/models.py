from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

from base.models import SoftDeleteModel
from product.models import ProductVariation

from stock.services import remove_stock, add_stock
from stock.models import StockMovement


class CashRegister(SoftDeleteModel):
    """
    Representa o 'Turno de Caixa' ou a 'Gaveta'.
    O operador não consegue vender sem uma sessão aberta.
    """

    class Status(models.TextChoices):
        OPEN = "OPEN", "Aberto"
        CLOSED = "CLOSED", "Fechado"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cash_sessions",
        verbose_name="Operador",
    )

    # Valores Monetários
    opening_balance = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Fundo de Troco (Abertura)"
    )
    closing_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor de Fechamento",
    )

    # Metadados de Tempo
    opened_at = models.DateTimeField(auto_now_add=True, verbose_name="Abertura")
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fechamento")

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN,
        verbose_name="Status",
    )

    class Meta:
        verbose_name = "Sessão de Caixa"
        verbose_name_plural = "Sessões de Caixa"
        ordering = ["-opened_at"]

    def __str__(self):
        return f"Caixa #{self.pk} - {self.user} ({self.get_status_display()})"

    def close_session(self, final_value):
        """Fecha o caixa e registra o valor final conferido."""
        if self.status == self.Status.CLOSED:
            raise ValidationError("Este caixa já está fechado.")

        self.closing_balance = final_value
        self.closed_at = timezone.now()
        self.status = self.Status.CLOSED
        self.save()


class Sale(SoftDeleteModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Rascunho"
        COMPLETED = "COMPLETED", "Concluída"
        CANCELED = "CANCELED", "Cancelada"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sales",
        verbose_name="Vendedor/Operador",
    )

    cash_register_session = models.ForeignKey(
        CashRegister,
        on_delete=models.PROTECT,
        related_name="sales",
        verbose_name="Sessão de Caixa",
        null=True,
        blank=True,
    )

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

    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Venda #{self.pk} - {self.user} ({self.get_status_display()})"

    def calculate_totals(self):
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
        Finaliza a venda e baixa o estoque utilizando o serviço de Stock.
        Gera histórico de movimentação do tipo 'VENDA'.
        """
        if self.status != self.Status.DRAFT:
            raise ValidationError("Apenas vendas em Rascunho podem ser concluídas.")

        if not self.items.exists():
            raise ValidationError("Não é possível concluir uma venda sem itens.")

        if not self.cash_register_session:
            raise ValidationError(
                "Não é possível finalizar venda sem uma sessão de caixa vinculada."
            )

        if self.cash_register_session.status != CashRegister.Status.OPEN:
            raise ValidationError("O caixa desta venda já está fechado.")

        # BAIXA DE ESTOQUE VIA SERVIÇO
        for item in self.items.all():
            try:
                # O remove_stock cuida do lock (select_for_update), validação e criação do log
                remove_stock(
                    product_variation_id=item.variation.pk,
                    quantity=item.quantity,
                    user=self.user,
                    movement_type=StockMovement.MovementType.VENDA,
                    notes=f"Venda PDV #{self.pk}",
                )
            except ValueError as e:
                # O serviço lança ValueError se faltar estoque ou dados inválidos
                raise ValidationError(
                    f"Erro ao processar item '{item.variation}': {str(e)}"
                )

        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    @transaction.atomic
    def cancel_sale(self):
        """
        Cancela a venda e devolve os itens ao estoque via serviço.
        Gera histórico de movimentação do tipo 'DEVOLUCAO'.
        """
        if self.status != self.Status.COMPLETED:
            raise ValidationError("Apenas vendas concluídas podem ser canceladas.")

        # DEVOLUÇÃO DE ESTOQUE VIA SERVIÇO
        for item in self.items.all():
            try:
                add_stock(
                    product_variation_id=item.variation.pk,
                    quantity=item.quantity,
                    user=self.user,
                    unit_price=item.unit_price,  # Valor que entra no estoque (baseado na venda)
                    movement_type=StockMovement.MovementType.DEVOLUCAO,
                    notes=f"Estorno da Venda #{self.pk}",
                )
            except ValueError as e:
                raise ValidationError(
                    f"Erro ao estornar item '{item.variation}': {str(e)}"
                )

        self.status = self.Status.CANCELED
        self.delete()


class SaleItem(models.Model):
    # O SaleItem permanece inalterado, pois é apenas a representação dos itens na venda
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    variation = models.ForeignKey(
        ProductVariation, on_delete=models.PROTECT, related_name="sale_items"
    )
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
            models.UniqueConstraint(
                fields=["sale", "variation"], name="unique_variation_per_sale"
            )
        ]

    def clean(self):
        if self.sale_id and self.sale.status != Sale.Status.DRAFT:
            raise ValidationError(
                "Não é possível alterar itens de uma venda finalizada."
            )

    def save(self, *args, **kwargs):
        self.clean()
        if not self.pk:
            self.product_sku_snapshot = self.variation.sku
            self.product_name_snapshot = str(self.variation)
            if self.unit_price is None:
                self.unit_price = self.variation.product.selling_price

        bruto = self.unit_price * self.quantity
        self.total_price = max(bruto - self.discount, Decimal("0.00"))

        super().save(*args, **kwargs)
        self.sale.calculate_totals()

    def delete(self, *args, **kwargs):
        if self.sale.status != Sale.Status.DRAFT:
            raise ValidationError(
                "Não é possível remover itens de uma venda finalizada."
            )
        super().delete(*args, **kwargs)
        self.sale.calculate_totals()
