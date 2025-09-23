from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Cor"
        verbose_name_plural = "Cores"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        verbose_name = "Tamanho"
        verbose_name_plural = "Tamanhos"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, related_name="products"
    )

    @property
    def profit_margin(self):
        """
        Calcula a margem de lucro dinamicamente como uma porcentagem.
        ex: retorna 20 para 20%
        """
        if self.selling_price > 0:
            profit = self.selling_price - self.cost_price
            margin = (profit / self.selling_price) * 100
            return round(margin, 2)

        return 0

    @property
    def total_stock(self):
        """
        Retorna o estoque total somando o estoque de todas as variações do produto.
        """
        return sum(variation.stock for variation in self.variations.all())
    
    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductVariation(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    stock = models.PositiveBigIntegerField(default=0, verbose_name="Estoque")
    minimum_stock = models.PositiveBigIntegerField(
        default=0, verbose_name="Estoque Mínimo"
    )
    product = models.ForeignKey(
        "Product", on_delete=models.CASCADE, related_name="variations"
    )
    color = models.ForeignKey(Color, on_delete=models.PROTECT)
    size = models.ForeignKey(Size, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Variação de Produto"
        verbose_name_plural = "Variações de Produtos"
        ordering = ["product", "color", "size"]
        unique_together = ("product", "color", "size")

    def __str__(self):
        return f"{self.product.name} - {self.color.name} - {self.size.name}"
