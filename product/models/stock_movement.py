from django.db import models
from .product import ProductVariation
from user.models import UserGesthar
from django.core.exceptions import ValidationError


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SAIDA = "SAIDA", "Saída"
        AJUSTE_SAIDA = "AJUSTE_SAIDA", "Ajuste (Saída)"
        AJUSTE_ENTRADA = "AJUSTE_ENTRADA", "Ajuste (Entrada)"
        DEVOLUCAO = "DEVOLUCAO", "Devolução"

    movement_type = models.CharField(
        max_length=20, choices=MovementType.choices, verbose_name="Tipo de Movimento"
    )
    quantity = models.PositiveIntegerField(verbose_name="Quantidade")
    product_variation = models.ForeignKey(
        ProductVariation,
        on_delete=models.CASCADE,
        related_name="stock_movements",
        verbose_name="Variação de Produto",
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Preço Unitário",
    )
    movement_date = models.DateTimeField(
        auto_now_add=True, verbose_name="Data do Movimento"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    user = models.ForeignKey(
        UserGesthar,
        on_delete=models.PROTECT,
        related_name="stock_movements",
        verbose_name="Usuário",
    )

    class Meta:
        verbose_name = "Movimento de Estoque"
        verbose_name_plural = "Movimentos de Estoque"
        ordering = ["-movement_date"]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product_variation.sku} - {self.quantity}"

    def clean(self):
        super().clean()

        errors = {}
        # Validação para garantir que a quantidade seja positiva
        if self.quantity <= 0:
            errors["quantity"] = ValidationError(
                "A quantidade deve ser um número positivo."
            )

        # Validação para garantir que o preço unitário seja fornecido para certos tipos de movimento
        if self.movement_type in {
            self.MovementType.ENTRADA,
            self.MovementType.AJUSTE_ENTRADA,
            self.MovementType.DEVOLUCAO,
        } and (self.unit_price is None or self.unit_price <= 0):
            errors["unit_price"] = ValidationError(
                "O preço unitário deve ser fornecido e ser positivo para entradas, ajustes de entrada e devoluções."
            )

        if errors:
            raise ValidationError(errors)
