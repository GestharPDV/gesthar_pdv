from django.test import TestCase
from product.utils.generate_sku import (
    generate_product_part,
    _generate_color_part,
    generate_size_part,
    generate_sku,
)
from product.utils.standardize_name import standardize_name
from product.models import Category, Product, ProductVariation, Color, Size
from decimal import Decimal


class GenerateProductPartTests(TestCase):
    """Testes para generate_product_part"""
    
    def test_nome_com_uma_palavra(self):
        """Teste SKU com nome de uma palavra"""
        result = generate_product_part("Camiseta")
        self.assertEqual(result, "CAM")
    
    def test_nome_com_duas_palavras(self):
        """Teste SKU com nome de duas palavras"""
        result = generate_product_part("Camiseta Branca")
        self.assertEqual(result, "CAMBR")
    
    def test_nome_com_tres_palavras(self):
        """Teste SKU com nome de três palavras"""
        result = generate_product_part("Camiseta Branca Algodao")
        self.assertEqual(result, "CAMBRA")
    
    def test_nome_com_multiplas_palavras(self):
        """Teste SKU com nome de múltiplas palavras"""
        result = generate_product_part("Camiseta Branca Algodao Premium Extra")
        self.assertEqual(result, "CAMBRAPE")
    
    def test_nome_minusculo_fica_maiusculo(self):
        """Teste que converte para maiúsculas"""
        result = generate_product_part("calça jeans")
        self.assertEqual(result, "CALJE")
    
    def test_palavra_com_menos_de_3_letras(self):
        """Teste palavra com menos de 3 letras"""
        result = generate_product_part("TV")
        self.assertEqual(result, "TV")


class GenerateColorPartTests(TestCase):
    """Testes para _generate_color_part"""
    
    def test_cor_simples(self):
        """Teste cor com uma palavra"""
        result = _generate_color_part("Azul")
        self.assertEqual(result, "A")
    
    def test_cor_composta(self):
        """Teste cor com múltiplas palavras"""
        result = _generate_color_part("Azul Marinho")
        self.assertEqual(result, "AM")
    
    def test_cor_na(self):
        """Teste cor N/A especial"""
        result = _generate_color_part("N/A")
        self.assertEqual(result, "NA")
    
    def test_cor_minuscula_fica_maiuscula(self):
        """Teste que converte para maiúsculas"""
        result = _generate_color_part("verde claro")
        self.assertEqual(result, "VC")


class GenerateSizePartTests(TestCase):
    """Testes para generate_size_part"""
    
    def test_tamanho_simples(self):
        """Teste tamanho simples"""
        result = generate_size_part("M")
        self.assertEqual(result, "M")
    
    def test_tamanho_g(self):
        """Teste tamanho G"""
        result = generate_size_part("G")
        self.assertEqual(result, "G")
    
    def test_tamanho_na(self):
        """Teste tamanho N/A especial"""
        result = generate_size_part("N/A")
        self.assertEqual(result, "UN")
    
    def test_tamanho_minusculo_fica_maiusculo(self):
        """Teste que converte para maiúsculas"""
        result = generate_size_part("gg")
        self.assertEqual(result, "GG")


class GenerateSKUTests(TestCase):
    """Testes para generate_sku (função completa)"""
    
    def setUp(self):
        """Configuração inicial"""
        self.category = Category.objects.create(name="Vestuário")
        self.product = Product.objects.create(
            name="Camiseta Branca",
            selling_price=Decimal("50.00"),
            category=self.category
        )
        self.color = Color.objects.create(name="Azul")
        self.size = Size.objects.create(name="M")
    
    def test_gerar_sku_completo(self):
        """Teste geração de SKU completo"""
        variation = ProductVariation(
            product=self.product,
            color=self.color,
            size=self.size
        )
        sku = generate_sku(variation)
        self.assertEqual(sku, "CAMBR-A-M")
    
    def test_sku_com_cor_composta(self):
        """Teste SKU com cor composta"""
        color = Color.objects.create(name="Azul Marinho")
        variation = ProductVariation(
            product=self.product,
            color=color,
            size=self.size
        )
        sku = generate_sku(variation)
        self.assertEqual(sku, "CAMBR-AM-M")
    
    def test_sku_com_produto_multiplas_palavras(self):
        """Teste SKU com produto de múltiplas palavras"""
        product = Product.objects.create(
            name="Calça Jeans Slim Fit",
            selling_price=Decimal("120.00"),
            category=self.category
        )
        variation = ProductVariation(
            product=product,
            color=self.color,
            size=self.size
        )
        sku = generate_sku(variation)
        self.assertEqual(sku, "CALJESF-A-M")
    
    def test_sku_gerado_automaticamente_ao_salvar(self):
        """Teste que SKU é gerado automaticamente ao salvar"""
        variation = ProductVariation.objects.create(
            product=self.product,
            color=self.color,
            size=self.size,
            stock=10
        )
        self.assertIsNotNone(variation.sku)
        self.assertEqual(variation.sku, "CAMBR-A-M")


class StandardizeNameTests(TestCase):
    """Testes para standardize_name"""
    
    def test_remover_espacos_extras(self):
        """Teste que remove espaços extras no início e fim"""
        result = standardize_name("  Produto  ")
        self.assertEqual(result, "Produto")
    
    def test_converter_para_title_case(self):
        """Teste que converte para Title Case"""
        result = standardize_name("produto teste")
        self.assertEqual(result, "Produto Teste")
    
    def test_nome_ja_normalizado(self):
        """Teste com nome já normalizado"""
        result = standardize_name("Produto Teste")
        self.assertEqual(result, "Produto Teste")
    
    def test_nome_todo_maiusculo(self):
        """Teste com nome todo em maiúsculas"""
        result = standardize_name("PRODUTO TESTE")
        self.assertEqual(result, "Produto Teste")
    
    def test_nome_com_espacos_multiplos_internos(self):
        """Teste com múltiplos espaços internos"""
        result = standardize_name("Produto    Teste")
        # title() mantém espaços internos, mas strip() remove externos
        self.assertIn("Produto", result)
        self.assertIn("Teste", result)

