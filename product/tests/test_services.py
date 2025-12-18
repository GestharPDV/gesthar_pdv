from django.test import TestCase
from product.services import (
    ServiceValidationError,
    ServiceDuplicateError,
    create_category,
    create_supplier,
    create_color,
    create_size,
    get_filtered_products,
)
from product.models import Category, Supplier, Color, Size, Product
from decimal import Decimal


class CreateCategoryServiceTests(TestCase):
    """Testes para o serviço create_category"""
    
    def test_criar_categoria_valida(self):
        """Teste criar categoria com nome válido"""
        category = create_category("Roupas")
        self.assertIsNotNone(category)
        self.assertEqual(category.name, "Roupas")
        self.assertTrue(category.is_active)
    
    def test_criar_categoria_nome_normalizado(self):
        """Teste que o nome é normalizado"""
        category = create_category("  roupas  ")
        self.assertEqual(category.name, "Roupas")
    
    def test_criar_categoria_sem_nome_levanta_erro(self):
        """Teste que nome vazio levanta ServiceValidationError"""
        with self.assertRaises(ServiceValidationError):
            create_category("")
        
        with self.assertRaises(ServiceValidationError):
            create_category("   ")
        
        with self.assertRaises(ServiceValidationError):
            create_category(None)
    
    def test_criar_categoria_duplicada_levanta_erro(self):
        """Teste que nome duplicado levanta ServiceDuplicateError"""
        create_category("Eletrônicos")
        with self.assertRaises(ServiceDuplicateError):
            create_category("Eletrônicos")
    
    def test_criar_categoria_duplicada_case_insensitive(self):
        """Teste que nomes com case diferente são considerados duplicados"""
        create_category("Livros")
        with self.assertRaises(ServiceDuplicateError):
            create_category("livros")


class CreateSupplierServiceTests(TestCase):
    """Testes para o serviço create_supplier"""
    
    def test_criar_fornecedor_valido(self):
        """Teste criar fornecedor com nome válido"""
        supplier = create_supplier("Fornecedor ABC")
        self.assertIsNotNone(supplier)
        self.assertEqual(supplier.name, "Fornecedor Abc")
        self.assertTrue(supplier.is_active)
    
    def test_criar_fornecedor_sem_nome_levanta_erro(self):
        """Teste que nome vazio levanta erro"""
        with self.assertRaises(ServiceValidationError):
            create_supplier("")
    
    def test_criar_fornecedor_duplicado_levanta_erro(self):
        """Teste que nome duplicado levanta erro"""
        create_supplier("Distribuidora XYZ")
        with self.assertRaises(ServiceDuplicateError):
            create_supplier("Distribuidora XYZ")


class CreateColorServiceTests(TestCase):
    """Testes para o serviço create_color"""
    
    def test_criar_cor_valida(self):
        """Teste criar cor com nome válido"""
        color = create_color("Azul Marinho")
        self.assertIsNotNone(color)
        self.assertEqual(color.name, "Azul Marinho")
    
    def test_criar_cor_sem_nome_levanta_erro(self):
        """Teste que nome vazio levanta erro"""
        with self.assertRaises(ServiceValidationError):
            create_color("")
    
    def test_criar_cor_duplicada_levanta_erro(self):
        """Teste que nome duplicado levanta erro"""
        create_color("Vermelho")
        with self.assertRaises(ServiceDuplicateError):
            create_color("Vermelho")


class CreateSizeServiceTests(TestCase):
    """Testes para o serviço create_size"""
    
    def test_criar_tamanho_valido(self):
        """Teste criar tamanho com nome válido"""
        size = create_size("M")
        self.assertIsNotNone(size)
        self.assertEqual(size.name, "M")
        self.assertTrue(size.is_active)
    
    def test_criar_tamanho_sem_nome_levanta_erro(self):
        """Teste que nome vazio levanta erro"""
        with self.assertRaises(ServiceValidationError):
            create_size("")
    
    def test_criar_tamanho_duplicado_levanta_erro(self):
        """Teste que nome duplicado levanta erro"""
        create_size("G")
        with self.assertRaises(ServiceDuplicateError):
            create_size("G")


class GetFilteredProductsServiceTests(TestCase):
    """Testes para o serviço get_filtered_products"""
    
    def setUp(self):
        """Configuração inicial"""
        self.category = Category.objects.create(name="Eletrônicos")
        self.product1 = Product.objects.create(
            name="Notebook",
            selling_price=Decimal("3000.00"),
            category=self.category
        )
        self.product2 = Product.objects.create(
            name="Mouse",
            selling_price=Decimal("50.00"),
            category=self.category
        )
        self.product3 = Product.objects.create(
            name="Teclado",
            selling_price=Decimal("150.00"),
            category=self.category
        )
    
    def test_buscar_produtos_sem_filtro(self):
        """Teste buscar todos os produtos sem filtro"""
        result = get_filtered_products()
        self.assertEqual(result['products'].paginator.count, 3)
    
    def test_buscar_produtos_por_nome(self):
        """Teste buscar produtos por nome"""
        result = get_filtered_products(query="Mouse")
        self.assertEqual(result['products'].paginator.count, 1)
        self.assertEqual(result['products'][0].name, "Mouse")
    
    def test_buscar_produtos_por_categoria(self):
        """Teste buscar produtos por categoria"""
        category2 = Category.objects.create(name="Roupas")
        Product.objects.create(
            name="Camiseta",
            selling_price=Decimal("50.00"),
            category=category2
        )
        
        result = get_filtered_products(query="Roupas")
        self.assertEqual(result['products'].paginator.count, 1)
    
    def test_paginacao_funciona(self):
        """Teste que a paginação funciona corretamente"""
        # Criar mais produtos para testar paginação
        for i in range(15):
            Product.objects.create(
                name=f"Produto {i}",
                selling_price=Decimal("100.00"),
                category=self.category
            )
        
        result = get_filtered_products(per_page=10, page_number=1)
        self.assertEqual(len(result['products']), 10)
        self.assertTrue(result['page_obj'].has_next())
    
    def test_busca_case_insensitive(self):
        """Teste que a busca não diferencia maiúsculas/minúsculas"""
        result = get_filtered_products(query="NOTEBOOK")
        self.assertEqual(result['products'].paginator.count, 1)
        
        result = get_filtered_products(query="notebook")
        self.assertEqual(result['products'].paginator.count, 1)

