from django.test import TestCase
from decimal import Decimal
from product.models import (
    Category,
    Product,
    ProductVariation,
    ProductSupplier,
    Supplier,
    Color,
    Size,
)


class ProductQuerySetTests(TestCase):
    """Testes para o ProductQuerySet (manager customizado)"""
    
    def setUp(self):
        """Configuração inicial"""
        self.category = Category.objects.create(name="Teste")
        self.product = Product.objects.create(
            name="Produto Teste",
            selling_price=Decimal("100.00"),
            category=self.category
        )
        self.color = Color.objects.create(name="Preto")
        self.size = Size.objects.create(name="M")
    
    def test_with_stock_sem_variacoes(self):
        """Teste que produto sem variações tem estoque zero"""
        products = Product.objects.with_stock()
        product = products.get(pk=self.product.pk)
        self.assertEqual(product.total_stock, 0)
    
    def test_with_stock_com_variacoes_ativas(self):
        """Teste que calcula estoque corretamente de variações ativas"""
        ProductVariation.objects.create(
            product=self.product,
            color=self.color,
            size=self.size,
            stock=50,
            is_active=True
        )
        size2 = Size.objects.create(name="G")
        ProductVariation.objects.create(
            product=self.product,
            color=self.color,
            size=size2,
            stock=30,
            is_active=True
        )
        
        products = Product.objects.with_stock()
        product = products.get(pk=self.product.pk)
        self.assertEqual(product.total_stock, 80)
    
    def test_with_stock_ignora_variacoes_inativas(self):
        """Teste que variações inativas não são contadas no estoque"""
        ProductVariation.objects.create(
            product=self.product,
            color=self.color,
            size=self.size,
            stock=50,
            is_active=True
        )
        size2 = Size.objects.create(name="G")
        ProductVariation.objects.create(
            product=self.product,
            color=self.color,
            size=size2,
            stock=100,
            is_active=False  # Inativa
        )
        
        products = Product.objects.with_stock()
        product = products.get(pk=self.product.pk)
        self.assertEqual(product.total_stock, 50)
    
    def test_with_average_profit_margin_sem_fornecedores(self):
        """Teste margem de lucro sem fornecedores"""
        products = Product.objects.with_average_profit_margin()
        product = products.get(pk=self.product.pk)
        self.assertEqual(product.average_cost_price, Decimal("0.00"))
        self.assertEqual(product.profit_margin, Decimal("100.00"))
    
    def test_with_average_profit_margin_com_fornecedor(self):
        """Teste cálculo de margem de lucro com fornecedor"""
        supplier = Supplier.objects.create(name="Fornecedor A")
        ProductSupplier.objects.create(
            product=self.product,
            supplier=supplier,
            cost_price=Decimal("60.00")
        )
        
        products = Product.objects.with_average_profit_margin()
        product = products.get(pk=self.product.pk)
        
        self.assertEqual(product.average_cost_price, Decimal("60.00"))
        # Margem = ((100 - 60) / 100) * 100 = 40%
        self.assertEqual(product.profit_margin, Decimal("40.00"))
    
    def test_with_average_profit_margin_multiplos_fornecedores(self):
        """Teste cálculo de custo médio com múltiplos fornecedores"""
        supplier1 = Supplier.objects.create(name="Fornecedor A")
        supplier2 = Supplier.objects.create(name="Fornecedor B")
        
        ProductSupplier.objects.create(
            product=self.product,
            supplier=supplier1,
            cost_price=Decimal("50.00")
        )
        ProductSupplier.objects.create(
            product=self.product,
            supplier=supplier2,
            cost_price=Decimal("70.00")
        )
        
        products = Product.objects.with_average_profit_margin()
        product = products.get(pk=self.product.pk)
        
        # Custo médio = (50 + 70) / 2 = 60
        self.assertEqual(product.average_cost_price, Decimal("60.00"))


class ActiveProductVariationManagerTests(TestCase):
    """Testes para o ActiveProductVariationManager"""
    
    def setUp(self):
        """Configuração inicial"""
        self.category = Category.objects.create(name="Teste")
        self.product = Product.objects.create(
            name="Produto Ativo",
            selling_price=Decimal("100.00"),
            category=self.category,
            is_active=True
        )
        self.product_inativo = Product.objects.create(
            name="Produto Inativo",
            selling_price=Decimal("100.00"),
            category=self.category,
            is_active=False
        )
        self.color = Color.objects.create(name="Azul")
        self.size = Size.objects.create(name="M")
    
    def test_retorna_apenas_variacoes_ativas(self):
        """Teste que retorna apenas variações ativas"""
        var_ativa = ProductVariation.objects.create(
            product=self.product,
            color=self.color,
            size=self.size,
            stock=10,
            is_active=True
        )
        size2 = Size.objects.create(name="G")
        ProductVariation.objects.create(
            product=self.product,
            color=self.color,
            size=size2,
            stock=20,
            is_active=False
        )
        
        active_variations = ProductVariation.active.all()
        self.assertEqual(active_variations.count(), 1)
        self.assertEqual(active_variations.first(), var_ativa)
    
    def test_ignora_variacoes_de_produtos_inativos(self):
        """Teste que ignora variações de produtos inativos"""
        ProductVariation.objects.create(
            product=self.product,
            color=self.color,
            size=self.size,
            stock=10,
            is_active=True
        )
        size2 = Size.objects.create(name="G")
        ProductVariation.objects.create(
            product=self.product_inativo,
            color=self.color,
            size=size2,
            stock=20,
            is_active=True
        )
        
        active_variations = ProductVariation.active.all()
        # Deve retornar apenas a variação do produto ativo
        self.assertEqual(active_variations.count(), 1)
        self.assertEqual(active_variations.first().product, self.product)

