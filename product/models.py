from django.db import models
from django.db.models import (
    Q,
    Sum,
    Case,
    When,
    F,
    ExpressionWrapper,
    DecimalField,
    Value,
    OuterRef,
    Avg,
    Subquery,
)
from django.db.models.functions import Coalesce
from django.forms import ValidationError
from product.mixins import StandardizeNameMixin
from .utils import generate_sku


# Managers
class ProductQuerySet(models.QuerySet):

    def with_stock(self):
        """
        Retorna o estoque total somando o estoque de todas as variações dos produtos no queryset.
        Garante que o resultado seja 0 em vez de None se não houver variações.
        """
        # Coalesce para substituir um resultado None (caso não haja variações) por 0.
        total = Coalesce(
            Sum("variations__stock", filter=Q(variations__is_active=True)), Value(0)
        )
        return self.annotate(total_stock=total)

    def with_average_profit_margin(self):
        """
        Anota a margem de lucro (%) e custo médio de cada produto,
        garantindo tipos compatíveis (DecimalField).
        """

        avg_cost_subquery = (
            ProductSupplier.objects.filter(product=OuterRef("pk"))
            .values("product")
            .annotate(avg_cost=Avg("cost_price"))
            .values("avg_cost")
        )

        queryset = self.annotate(
            average_cost_price=Coalesce(
                Subquery(
                    avg_cost_subquery,
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                ),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)),
            )
        )

        # 🔢 Calcular margem de lucro com tipos Decimal coerentes
        profit = ExpressionWrapper(
            F("selling_price") - F("average_cost_price"),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )

        margin_expression = ExpressionWrapper(
            (
                profit
                * Value(100, output_field=DecimalField(max_digits=5, decimal_places=2))
            )
            / F("selling_price"),
            output_field=DecimalField(max_digits=5, decimal_places=2),
        )

        return queryset.annotate(
            profit_margin=Case(
                When(
                    selling_price__gt=0,
                    then=margin_expression,
                ),
                default=Value(
                    0, output_field=DecimalField(max_digits=5, decimal_places=2)
                ),
            )
        )


class ActiveProductVariationManager(models.Manager):
    """Manager que retorna apenas as variações de produto ativas."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


# Models
class Category(StandardizeNameMixin, models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Color(StandardizeNameMixin, models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nome")

    class Meta:
        verbose_name = "Cor"
        verbose_name_plural = "Cores"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Size(StandardizeNameMixin, models.Model):
    name = models.CharField(max_length=50, verbose_name="Nome")
    code = models.CharField(max_length=10, unique=True, verbose_name="Código")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Tamanho"
        verbose_name_plural = "Tamanhos"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.code:
            self.code = self.code.strip().upper()


class Supplier(StandardizeNameMixin, models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(StandardizeNameMixin, models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
    selling_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Preço de Venda"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Categoria",
    )
    suppliers = models.ManyToManyField(
        Supplier, through="ProductSupplier", related_name="products"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    has_variation = models.BooleanField(default=False, verbose_name="Possui Variação")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if hasattr(self.category, "is_active") and not self.category.is_active:
            raise ValidationError(
                {
                    "category": "Não é possível associar o produto a uma categoria inativa."
                }
            )


class ProductSupplier(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    cost_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Preço de Custo do Fornecedor"
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Adicionado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Fornecedor do Produto"
        verbose_name_plural = "Fornecedores do Produto"
        constraints = [
            # Garante que não se pode adicionar o mesmo fornecedor duas vezes ao mesmo produto.
            models.UniqueConstraint(
                fields=["product", "supplier"], name="prod_supplier_unique_link_uq"
            )
        ]

    def __str__(self):
        return f"{self.product.name} (Fornecedor: {self.supplier.name})"


class ProductVariation(models.Model):
    sku = models.CharField(
        max_length=50, unique=True, editable=False, blank=True, verbose_name="SKU"
    )
    stock = models.PositiveBigIntegerField(default=0, verbose_name="Estoque")
    minimum_stock = models.PositiveBigIntegerField(
        default=0, verbose_name="Estoque Mínimo"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variations"
    )
    color = models.ForeignKey(Color, on_delete=models.PROTECT, verbose_name="Cor")
    size = models.ForeignKey(Size, on_delete=models.PROTECT, verbose_name="Tamanho")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    objects = models.Manager()  # Manager padrão
    active = ActiveProductVariationManager()  # Manager customizado

    class Meta:
        verbose_name = "Variação de Produto"
        verbose_name_plural = "Variações de Produtos"
        ordering = ["product", "color", "size"]

        constraints = [
            # Garantir que o estoque e o estoque mínimo não sejam negativos
            models.CheckConstraint(
                check=models.Q(stock__gte=0) & models.Q(minimum_stock__gte=0),
                name="stock_non_negative",
            ),
            # Garantir que uma combinação única de produto, cor e tamanho exista
            models.UniqueConstraint(
                fields=["product", "color", "size"], name="unique_product_color_size"
            ),
        ]

    def __str__(self):
        product_name = self.product.name if self.product else "Produto Inválido"
        color_name = self.color.name if self.color else "Sem Cor"
        size_name = self.size.name if self.size else "Sem Tamanho"
        return f"{product_name} - {color_name} - {size_name}"

    def save(self, *args, **kwargs):
        # Gera o SKU apenas se não estiver definido
        if not self.sku:
            self.sku = generate_sku(self)
        super().save(*args, **kwargs)
