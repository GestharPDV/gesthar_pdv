from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
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

User = get_user_model()


class ProductIntegrationTests(TestCase):
    """Testes de integração - fluxo completo"""
    
    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='admin@exemplo.com',
            password='admin123'
        )
        self.category = Category.objects.create(name="Roupas")
        self.supplier = Supplier.objects.create(name="Fornecedor A")
        self.color = Color.objects.create(name="Azul")
        self.size = Size.objects.create(name="M")
    
    def test_fluxo_completo_criar_produto_com_variacoes(self):
        """Teste fluxo completo: criar produto com variações e fornecedores"""
        self.client.login(username='admin@exemplo.com', password='admin123')
        
        # Criar produto
        product = Product.objects.create(
            name="Camiseta Premium",
            description="Camiseta de alta qualidade",
            selling_price=Decimal("89.90"),
            category=self.category
        )
        
        # Adicionar fornecedor
        ProductSupplier.objects.create(
            product=product,
            supplier=self.supplier,
            cost_price=Decimal("45.00")
        )
        
        # Criar variação
        variation = ProductVariation.objects.create(
            product=product,
            color=self.color,
            size=self.size,
            stock=50,
            minimum_stock=10
        )
        
        # Verificar que tudo foi criado
        self.assertTrue(Product.objects.filter(name="Camiseta Premium").exists())
        self.assertEqual(product.productsupplier_set.count(), 1)
        self.assertEqual(product.variations.count(), 1)
        self.assertIsNotNone(variation.sku)
        
        # Verificar anotações
        products = Product.objects.with_stock().with_average_profit_margin()
        product_annotated = products.get(pk=product.pk)
        self.assertEqual(product_annotated.total_stock, 50)
        self.assertEqual(product_annotated.average_cost_price, Decimal("45.00"))
    
    def test_fluxo_buscar_e_visualizar_produto(self):
        """Teste fluxo: buscar produto e visualizar detalhes"""
        self.client.login(username='admin@exemplo.com', password='admin123')
        
        # Criar produto
        product = Product.objects.create(
            name="Calça Jeans",
            selling_price=Decimal("150.00"),
            category=self.category
        )
        
        # Buscar produto na lista
        list_url = reverse('product:product-list')
        response = self.client.get(list_url, {'query': 'Jeans'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Calça Jeans")
        
        # Visualizar detalhes
        detail_url = reverse('product:product-detail', kwargs={'pk': product.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Calça Jeans")
        self.assertContains(response, "150")
    
    def test_produto_com_multiplas_variacoes(self):
        """Teste produto com múltiplas variações (cores e tamanhos)"""
        product = Product.objects.create(
            name="Polo Basica",
            selling_price=Decimal("69.90"),
            category=self.category
        )
        
        # Criar cores e tamanhos únicos para este teste
        color_vermelho = Color.objects.create(name="Vermelho Escuro") 
        # Verde Claro -> VC
        color_verde = Color.objects.create(name="Verde Claro")
        size_p = Size.objects.create(name="PP")
        size_g = Size.objects.create(name="GG")
        
        # Criar todas as combinações
        ProductVariation.objects.create(
            product=product,
            color=color_vermelho,
            size=size_p,
            stock=25
        )
        ProductVariation.objects.create(
            product=product,
            color=color_vermelho,
            size=size_g,
            stock=25
        )
        ProductVariation.objects.create(
            product=product,
            color=color_verde,
            size=size_p,
            stock=25
        )
        ProductVariation.objects.create(
            product=product,
            color=color_verde,
            size=size_g,
            stock=25
        )
        
        # Verificar
        self.assertEqual(product.variations.count(), 4)
        
        # Verificar estoque total
        products = Product.objects.with_stock()
        product_with_stock = products.get(pk=product.pk)
        self.assertEqual(product_with_stock.total_stock, 100)  # 4 variações x 25
    
    def test_sku_unico_por_variacao(self):
        """Teste que cada variação tem SKU único"""
        product = Product.objects.create(
            name="Bermuda",
            selling_price=Decimal("79.90"),
            category=self.category
        )
        
        var1 = ProductVariation.objects.create(
            product=product,
            color=self.color,
            size=self.size,
            stock=10
        )
        
        color2 = Color.objects.create(name="Preto")
        var2 = ProductVariation.objects.create(
            product=product,
            color=color2,
            size=self.size,
            stock=15
        )
        
        # SKUs devem ser diferentes
        self.assertNotEqual(var1.sku, var2.sku)
        # SKUs devem existir
        self.assertIsNotNone(var1.sku)
        self.assertIsNotNone(var2.sku)
    
    def test_calculos_margem_lucro(self):
        """Teste cálculo de margem de lucro com diferentes cenários"""
        product = Product.objects.create(
            name="Produto Teste",
            selling_price=Decimal("100.00"),
            category=self.category
        )
        
        # Sem fornecedores - margem deve ser 100%
        products = Product.objects.with_average_profit_margin()
        p = products.get(pk=product.pk)
        self.assertEqual(p.profit_margin, Decimal("100.00"))
        
        # Com um fornecedor
        supplier = Supplier.objects.create(name="Fornecedor B")
        ProductSupplier.objects.create(
            product=product,
            supplier=supplier,
            cost_price=Decimal("80.00")
        )
        
        products = Product.objects.with_average_profit_margin()
        p = products.get(pk=product.pk)
        self.assertEqual(p.average_cost_price, Decimal("80.00"))
        # Margem = (100 - 80) / 100 * 100 = 20%
        self.assertEqual(p.profit_margin, Decimal("20.00"))

