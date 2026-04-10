from django.test import TestCase
from django.urls import reverse

from product.models import Category, Color, Size, Product, ProductVariation
from user.models import UserGesthar
from stock.models import StockMovement
from stock import services


class StockReportViewTest(TestCase):
    """Testes de integração para a view StockReportView (RF016)."""

    @classmethod
    def setUpTestData(cls):
        # Usuário autenticado necessário (LoginRequiredMixin)
        cls.user = UserGesthar.objects.create_user(
            username="tester",
            password="testpass123",
        )

        # Fixtures mínimas para os serviços funcionarem
        cls.category = Category.objects.create(name="Roupas")
        cls.color = Color.objects.create(name="Rosa")
        cls.size = Size.objects.create(name="M")
        cls.product = Product.objects.create(
            name="Blusa Gestante",
            selling_price="59.90",
            category=cls.category,
        )
        cls.variation = ProductVariation.objects.create(
            product=cls.product,
            color=cls.color,
            size=cls.size,
            stock=10,
            minimum_stock=5,
        )

    def setUp(self):
        self.client.login(username="tester", password="testpass123")

    # ------------------------------------------------------------------
    # Testes da View
    # ------------------------------------------------------------------

    def test_url_retorna_200(self):
        """A rota stock:report-stock deve responder com HTTP 200."""
        url = reverse("stock:report-stock")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_contexto_contem_chaves_json_dos_graficos(self):
        """O contexto deve conter as chaves JSON para os gráficos."""
        url = reverse("stock:report-stock")
        response = self.client.get(url)
        self.assertIn("category_chart_json", response.context)
        self.assertIn("color_chart_json", response.context)

    def test_contexto_contem_total_de_pecas(self):
        """O contexto deve conter o total de peças em estoque."""
        url = reverse("stock:report-stock")
        response = self.client.get(url)
        self.assertIn("total_pieces", response.context)
        self.assertGreaterEqual(response.context["total_pieces"], 0)

    def test_contexto_contem_valoracao_do_estoque(self):
        """O contexto deve conter a valoração total do estoque."""
        url = reverse("stock:report-stock")
        response = self.client.get(url)
        self.assertIn("inventory_valuation", response.context)

    def test_redireciona_usuario_nao_autenticado(self):
        """Usuário não autenticado deve ser redirecionado para o login."""
        self.client.logout()
        url = reverse("stock:report-stock")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    # ------------------------------------------------------------------
    # Testes dos Serviços
    # ------------------------------------------------------------------

    def test_get_total_pieces(self):
        """get_total_pieces() deve somar o estoque de todas as variações ativas."""
        total = services.get_total_pieces()
        self.assertEqual(total, 10)

    def test_get_inventory_valuation(self):
        """get_inventory_valuation() deve retornar stock × selling_price."""
        import decimal
        valuation = services.get_inventory_valuation()
        expected = decimal.Decimal("10") * decimal.Decimal("59.90")
        self.assertAlmostEqual(float(valuation), float(expected), places=2)

    def test_get_low_stock_variations_retorna_vazia_quando_ok(self):
        """Sem variações abaixo do mínimo, a queryset deve estar vazia."""
        # estoque=10, minimum_stock=5 → não é baixo
        qs = services.get_low_stock_variations()
        self.assertEqual(qs.count(), 0)

    def test_get_low_stock_variations_detecta_estoque_baixo(self):
        """Deve detectar variação cujo estoque <= minimum_stock."""
        self.variation.stock = 3  # abaixo do mínimo (5)
        self.variation.save()
        qs = services.get_low_stock_variations()
        self.assertIn(self.variation, qs)
        # Restaurar para não afetar outros testes
        self.variation.stock = 10
        self.variation.save()

    def test_get_quantity_by_category(self):
        """get_quantity_by_category() deve agrupar corretamente por categoria."""
        data = services.get_quantity_by_category()
        self.assertIn("Roupas", data)
        self.assertEqual(data["Roupas"], 10)

    def test_get_quantity_by_color(self):
        """get_quantity_by_color() deve agrupar corretamente por cor."""
        data = services.get_quantity_by_color()
        self.assertIn("Rosa", data)
        self.assertEqual(data["Rosa"], 10)
