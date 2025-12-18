from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
import json
from product.models import (
    Category,
    Product,
    Supplier,
    Color,
    Size,
    ProductVariation,
)

User = get_user_model()


class ProductListViewTests(TestCase):
    """Testes para a view product_list_view"""
    
    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='teste@exemplo.com',
            password='senha123'
        )
        self.list_url = reverse('product:product-list')
        self.category = Category.objects.create(name="Teste")
        self.product = Product.objects.create(
            name="Produto 1",
            selling_price=Decimal("100.00"),
            category=self.category
        )
    
    def test_lista_requer_autenticacao(self):
        """Teste que lista requer login"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)  # Redireciona para login
    
    def test_lista_com_usuario_autenticado(self):
        """Teste lista com usuário autenticado"""
        self.client.login(username='teste@exemplo.com', password='senha123')
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'product/product_list.html')
    
    def test_lista_exibe_produtos(self):
        """Teste que lista exibe produtos"""
        self.client.login(username='teste@exemplo.com', password='senha123')
        response = self.client.get(self.list_url)
        self.assertContains(response, "Produto 1")
    
    def test_lista_com_busca(self):
        """Teste lista com parâmetro de busca"""
        Product.objects.create(
            name="Produto 2",
            selling_price=Decimal("150.00"),
            category=self.category
        )
        self.client.login(username='teste@exemplo.com', password='senha123')
        response = self.client.get(self.list_url, {'query': 'Produto 2'})
        self.assertContains(response, "Produto 2")


class ProductDetailViewTests(TestCase):
    """Testes para a view product_detail_view"""
    
    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='teste@exemplo.com',
            password='senha123'
        )
        self.category = Category.objects.create(name="Teste")
        self.product = Product.objects.create(
            name="Produto Detalhe",
            selling_price=Decimal("200.00"),
            category=self.category
        )
        self.detail_url = reverse('product:product-detail', kwargs={'pk': self.product.pk})
    
    def test_detalhe_requer_autenticacao(self):
        """Teste que detalhe requer login"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 302)
    
    def test_detalhe_com_usuario_autenticado(self):
        """Teste detalhe com usuário autenticado"""
        self.client.login(username='teste@exemplo.com', password='senha123')
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'product/product_detail.html')
    
    def test_detalhe_exibe_informacoes(self):
        """Teste que detalhe exibe informações do produto"""
        self.client.login(username='teste@exemplo.com', password='senha123')
        response = self.client.get(self.detail_url)
        self.assertContains(response, "Produto Detalhe")
        self.assertContains(response, "200")


class CategoryCreateAjaxViewTests(TestCase):
    """Testes para a view AJAX category_create_view"""
    
    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='teste@exemplo.com',
            password='senha123'
        )
        self.create_url = reverse('product:category-create')
    
    def test_criar_categoria_requer_autenticacao(self):
        """Teste que criação requer login"""
        response = self.client.post(
            self.create_url,
            data=json.dumps({'name': 'Nova Categoria'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)
    
    def test_criar_categoria_ajax_valida(self):
        """Teste criar categoria via AJAX com dados válidos"""
        self.client.login(username='teste@exemplo.com', password='senha123')
        response = self.client.post(
            self.create_url,
            data=json.dumps({'name': 'Eletrônicos'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['name'], 'Eletrônicos')
        self.assertTrue(Category.objects.filter(name='Eletrônicos').exists())
    
    def test_criar_categoria_ajax_nome_vazio(self):
        """Teste criar categoria com nome vazio retorna erro"""
        self.client.login(username='teste@exemplo.com', password='senha123')
        response = self.client.post(
            self.create_url,
            data=json.dumps({'name': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
    
    def test_criar_categoria_ajax_duplicada(self):
        """Teste criar categoria duplicada retorna erro"""
        Category.objects.create(name='Já Existe')
        self.client.login(username='teste@exemplo.com', password='senha123')
        response = self.client.post(
            self.create_url,
            data=json.dumps({'name': 'Já Existe'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')


class SupplierCreateAjaxViewTests(TestCase):
    """Testes para a view AJAX supplier_create_view"""
    
    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='teste@exemplo.com',
            password='senha123'
        )
        self.create_url = reverse('product:supplier-create')
    
    def test_criar_fornecedor_ajax_valido(self):
        """Teste criar fornecedor via AJAX"""
        self.client.login(username='teste@exemplo.com', password='senha123')
        response = self.client.post(
            self.create_url,
            data=json.dumps({'name': 'Fornecedor Novo'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(Supplier.objects.filter(name='Fornecedor Novo').exists())


class ColorCreateAjaxViewTests(TestCase):
    """Testes para a view AJAX color_create_view"""
    
    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='teste@exemplo.com',
            password='senha123'
        )
        self.create_url = reverse('product:color-create')
    
    def test_criar_cor_ajax_valida(self):
        """Teste criar cor via AJAX"""
        self.client.login(username='teste@exemplo.com', password='senha123')
        response = self.client.post(
            self.create_url,
            data=json.dumps({'name': 'Verde Limão'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(Color.objects.filter(name='Verde Limão').exists())


class SizeCreateAjaxViewTests(TestCase):
    """Testes para a view AJAX size_create_view"""
    
    def setUp(self):
        """Configuração inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='teste@exemplo.com',
            password='senha123'
        )
        self.create_url = reverse('product:size-create')
    
    def test_criar_tamanho_ajax_valido(self):
        """Teste criar tamanho via AJAX"""
        self.client.login(username='teste@exemplo.com', password='senha123')
        response = self.client.post(
            self.create_url,
            data=json.dumps({'name': 'XXG'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(Size.objects.filter(name='Xxg').exists())

