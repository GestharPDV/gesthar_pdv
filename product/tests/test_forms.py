from django.test import TestCase
from decimal import Decimal
from product.forms import (
    ProductForm,
    ProductSupplierForm,
    ProductVariationForm,
    ProductSupplierFormSet,
    ProductVariationFormSet,
)
from product.models import (
    Category,
    Supplier,
    Product,
    Color,
    Size,
)


class ProductFormTests(TestCase):
    """Testes para o formulário ProductForm"""
    
    def setUp(self):
        """Configuração inicial"""
        self.category = Category.objects.create(name="Teste", is_active=True)
        self.category_inativa = Category.objects.create(name="Inativa", is_active=False)
    
    def test_form_valido(self):
        """Teste formulário com dados válidos"""
        form_data = {
            'name': 'Produto Teste',
            'description': 'Descrição do produto',
            'selling_price': '100.00',
            'category': self.category.id,
            'is_active': True,
        }
        form = ProductForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_apenas_categorias_ativas(self):
        """Teste que queryset só contém categorias ativas"""
        form = ProductForm()
        categories = form.fields['category'].queryset
        self.assertIn(self.category, categories)
        self.assertNotIn(self.category_inativa, categories)
    
    def test_form_sem_nome_invalido(self):
        """Teste formulário sem nome é inválido"""
        form_data = {
            'selling_price': '100.00',
            'category': self.category.id,
        }
        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_form_sem_preco_invalido(self):
        """Teste formulário sem preço é inválido"""
        form_data = {
            'name': 'Produto',
            'category': self.category.id,
        }
        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('selling_price', form.errors)


class ProductSupplierFormTests(TestCase):
    """Testes para o formulário ProductSupplierForm"""
    
    def setUp(self):
        """Configuração inicial"""
        self.supplier = Supplier.objects.create(name="Fornecedor", is_active=True)
        self.supplier_inativo = Supplier.objects.create(name="Inativo", is_active=False)
    
    def test_form_valido(self):
        """Teste formulário com dados válidos"""
        form_data = {
            'supplier': self.supplier.id,
            'cost_price': '50.00',
        }
        form = ProductSupplierForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_apenas_fornecedores_ativos(self):
        """Teste que queryset só contém fornecedores ativos"""
        form = ProductSupplierForm()
        suppliers = form.fields['supplier'].queryset
        self.assertIn(self.supplier, suppliers)
        self.assertNotIn(self.supplier_inativo, suppliers)


class ProductVariationFormTests(TestCase):
    """Testes para o formulário ProductVariationForm"""
    
    def setUp(self):
        """Configuração inicial"""
        self.color = Color.objects.create(name="Azul")
        self.size = Size.objects.create(name="M", is_active=True)
        self.size_inativo = Size.objects.create(name="G", is_active=False)
    
    def test_form_valido(self):
        """Teste formulário com dados válidos"""
        form_data = {
            'color': self.color.id,
            'size': self.size.id,
            'stock': 100,
            'minimum_stock': 10,
            'is_active': True,
        }
        form = ProductVariationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_apenas_tamanhos_ativos(self):
        """Teste que queryset de tamanhos só contém ativos"""
        form = ProductVariationForm()
        sizes = form.fields['size'].queryset
        self.assertIn(self.size, sizes)
        self.assertNotIn(self.size_inativo, sizes)
    
    def test_form_todas_cores_disponiveis(self):
        """Teste que todas as cores estão disponíveis"""
        form = ProductVariationForm()
        colors = form.fields['color'].queryset
        self.assertIn(self.color, colors)


class ProductVariationFormSetTests(TestCase):
    """Testes para o ProductVariationFormSet"""
    
    def setUp(self):
        """Configuração inicial"""
        self.category = Category.objects.create(name="Teste")
        self.product = Product.objects.create(
            name="Produto",
            selling_price=Decimal("100.00"),
            category=self.category
        )
        self.color = Color.objects.create(name="Azul")
        self.size1 = Size.objects.create(name="M")
        self.size2 = Size.objects.create(name="G")
    
    def test_formset_valido(self):
        """Teste formset com dados válidos"""
        formset_data = {
            'variations-TOTAL_FORMS': '2',
            'variations-INITIAL_FORMS': '0',
            'variations-MIN_NUM_FORMS': '1',
            'variations-MAX_NUM_FORMS': '1000',
            'variations-0-color': self.color.id,
            'variations-0-size': self.size1.id,
            'variations-0-stock': 10,
            'variations-0-minimum_stock': 5,
            'variations-0-is_active': True,
            'variations-1-color': self.color.id,
            'variations-1-size': self.size2.id,
            'variations-1-stock': 20,
            'variations-1-minimum_stock': 10,
            'variations-1-is_active': True,
        }
        formset = ProductVariationFormSet(formset_data, instance=self.product, prefix='variations')
        self.assertTrue(formset.is_valid())
    
    def test_formset_variacoes_duplicadas_invalido(self):
        """Teste que variações duplicadas (mesma cor e tamanho) são inválidas"""
        formset_data = {
            'variations-TOTAL_FORMS': '2',
            'variations-INITIAL_FORMS': '0',
            'variations-MIN_NUM_FORMS': '1',
            'variations-MAX_NUM_FORMS': '1000',
            'variations-0-color': self.color.id,
            'variations-0-size': self.size1.id,
            'variations-0-stock': 10,
            'variations-0-minimum_stock': 5,
            'variations-0-is_active': True,
            'variations-1-color': self.color.id,
            'variations-1-size': self.size1.id,  # Mesma cor e tamanho
            'variations-1-stock': 20,
            'variations-1-minimum_stock': 10,
            'variations-1-is_active': True,
        }
        formset = ProductVariationFormSet(formset_data, instance=self.product, prefix='variations')
        self.assertFalse(formset.is_valid())

