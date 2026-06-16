import json
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse

from catalog.models import CatalogConfig
from product.models import Category, Color, Size, Product, ProductVariation


def make_product(name="Blusa Rosa", price="49.90", stock=10):
    category, _ = Category.objects.get_or_create(name="Roupas")
    color, _ = Color.objects.get_or_create(name="Rosa")
    size, _ = Size.objects.get_or_create(name="M")
    product, _ = Product.objects.get_or_create(
        name=name, defaults={"selling_price": price, "category": category}
    )
    ProductVariation.objects.get_or_create(
        product=product,
        color=color,
        size=size,
        defaults={"stock": stock},
    )
    return product


class TestCatalogListView(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("catalog:catalog-list")

    def test_returns_200_without_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_context_contains_only_products_with_stock(self):
        p_with = make_product("Calça Jeans", stock=5)
        p_without = make_product("Camiseta Sem Estoque", stock=0)
        response = self.client.get(self.url)
        product_ids = [p.pk for p in response.context["products"]]
        self.assertIn(p_with.pk, product_ids)
        self.assertNotIn(p_without.pk, product_ids)

    def test_context_includes_filters(self):
        make_product()
        response = self.client.get(self.url)
        self.assertIn("types", response.context)
        self.assertIn("colors", response.context)
        self.assertIn("sizes", response.context)


class TestProductDetailView(TestCase):
    def setUp(self):
        self.client = Client()

    def test_returns_json_for_product_with_stock(self):
        product = make_product()
        url = reverse("catalog:product-detail", args=[product.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["id"], product.pk)
        self.assertIn("variations", data)
        self.assertIn("images", data)

    def test_returns_404_for_product_without_stock(self):
        product = make_product("Sem Estoque 2", stock=0)
        url = reverse("catalog:product-detail", args=[product.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_returns_404_for_nonexistent_product(self):
        url = reverse("catalog:product-detail", args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class TestSearchProductsView(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("catalog:search-products")

    def test_returns_results_by_name(self):
        make_product("Vestido Floral")
        response = self.client.get(self.url, {"q": "vestido"})
        data = json.loads(response.content)
        self.assertTrue(any("Vestido" in p["name"] for p in data["products"]))

    def test_empty_query_returns_products(self):
        make_product()
        response = self.client.get(self.url, {"q": ""})
        data = json.loads(response.content)
        self.assertIsInstance(data["products"], list)

    def test_no_results_returns_empty_list(self):
        response = self.client.get(self.url, {"q": "xyzzy_produto_inexistente"})
        data = json.loads(response.content)
        self.assertEqual(data["products"], [])


class TestFilterProductsView(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("catalog:filter-products")

    def test_filter_by_type_returns_correct_products(self):
        make_product("Saia Rodada")
        response = self.client.get(self.url, {"type": "Roupas"})
        data = json.loads(response.content)
        self.assertIsInstance(data["products"], list)

    def test_filter_by_price_max(self):
        make_product("Produto Caro", price="999.00")
        make_product("Produto Barato", price="29.00")
        response = self.client.get(self.url, {"price_max": "50"})
        data = json.loads(response.content)
        for p in data["products"]:
            self.assertLessEqual(float(p["price"]), 50)

    def test_sort_by_price_asc(self):
        make_product("Prod B", price="100.00")
        make_product("Prod A", price="20.00")
        response = self.client.get(self.url, {"sort_by": "price_asc"})
        data = json.loads(response.content)
        prices = [float(p["price"]) for p in data["products"]]
        self.assertEqual(prices, sorted(prices))

    def test_only_products_with_stock_returned(self):
        make_product("Com Estoque", stock=3)
        make_product("Sem Estoque 3", stock=0)
        response = self.client.get(self.url)
        data = json.loads(response.content)
        for p in data["products"]:
            self.assertGreater(p["total_stock"], 0)


class TestWhatsAppRedirectView(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("catalog:whatsapp-redirect")
        CatalogConfig.objects.create(
            whatsapp_number="5511999999999",
            company_name="Loja Teste",
        )

    def _post(self, payload):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_valid_order_returns_whatsapp_url(self):
        product = make_product()
        variation = product.variations.first()
        payload = {
            "items": [
                {
                    "product_id": product.pk,
                    "variation_id": variation.pk,
                    "quantity": 1,
                }
            ]
        }
        response = self._post(payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("url", data)
        self.assertIn("wa.me", data["url"])

    def test_empty_cart_returns_400(self):
        response = self._post({"items": []})
        self.assertEqual(response.status_code, 400)

    def test_nonexistent_product_returns_400(self):
        payload = {"items": [{"product_id": 99999, "variation_id": None, "quantity": 1}]}
        response = self._post(payload)
        self.assertEqual(response.status_code, 400)

    def test_insufficient_stock_returns_400(self):
        product = make_product(stock=1)
        variation = product.variations.first()
        payload = {
            "items": [
                {
                    "product_id": product.pk,
                    "variation_id": variation.pk,
                    "quantity": 100,
                }
            ]
        }
        response = self._post(payload)
        self.assertEqual(response.status_code, 400)

    def test_message_contains_product_name(self):
        product = make_product("Blusa Teste WhatsApp")
        variation = product.variations.first()
        payload = {
            "items": [
                {
                    "product_id": product.pk,
                    "variation_id": variation.pk,
                    "quantity": 2,
                }
            ]
        }
        response = self._post(payload)
        data = json.loads(response.content)
        self.assertIn("Blusa+Teste+WhatsApp", data["url"].replace("%20", "+").replace("%2B", "+"))
