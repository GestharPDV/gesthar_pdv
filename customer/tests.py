from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from customer.models import Customer
from sales.models import Sale, CashRegister
from user.models import UserGesthar


class CustomerDetailViewTest(TestCase):
    """Testes de integração para a CustomerDetailView com histórico de compras real."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserGesthar.objects.create_user(
            email="tester@test.com",
            password="testpass123",
        )
        cls.customer = Customer.objects.create(
            name="Cliente Teste",
            cpf_cnpj="123.456.789-09",
            email="cliente@test.com",
        )
        cls.cash_register = CashRegister.objects.create(
            user=cls.user,
            opening_balance=Decimal("100.00"),
        )
        cls.sale_completed_1 = Sale.objects.create(
            user=cls.user,
            customer=cls.customer,
            cash_register_session=cls.cash_register,
            status=Sale.Status.COMPLETED,
            net_amount=Decimal("150.00"),
        )
        cls.sale_completed_2 = Sale.objects.create(
            user=cls.user,
            customer=cls.customer,
            cash_register_session=cls.cash_register,
            status=Sale.Status.COMPLETED,
            net_amount=Decimal("250.00"),
        )
        cls.sale_draft = Sale.objects.create(
            user=cls.user,
            customer=cls.customer,
            cash_register_session=cls.cash_register,
            status=Sale.Status.DRAFT,
            net_amount=Decimal("99.00"),
        )

    def setUp(self):
        self.client.force_login(self.user)

    def _get_response(self):
        url = reverse("customer:customer_detail", kwargs={"pk": self.customer.pk})
        return self.client.get(url)

    def test_url_retorna_200(self):
        self.assertEqual(self._get_response().status_code, 200)

    def test_total_purchases_ignora_rascunho(self):
        """Apenas vendas COMPLETED devem ser contadas."""
        response = self._get_response()
        self.assertEqual(response.context["total_purchases"], 2)

    def test_total_spent_soma_apenas_concluidas(self):
        """O valor total deve somar apenas as vendas COMPLETED."""
        response = self._get_response()
        self.assertEqual(response.context["total_spent"], Decimal("400.00"))

    def test_purchase_history_exclui_rascunho(self):
        """O histórico não deve conter a venda em rascunho."""
        response = self._get_response()
        ids = [s.id for s in response.context["purchase_history"]]
        self.assertIn(self.sale_completed_1.id, ids)
        self.assertIn(self.sale_completed_2.id, ids)
        self.assertNotIn(self.sale_draft.id, ids)

    def test_monthly_average_calculado(self):
        """O ticket médio deve ser a média do net_amount das vendas concluídas."""
        response = self._get_response()
        self.assertEqual(response.context["monthly_average"], Decimal("200.00"))

    def test_cliente_sem_compras_retorna_zeros(self):
        """Cliente sem vendas deve retornar total_purchases=0 e total_spent=0."""
        novo_cliente = Customer.objects.create(
            name="Sem Compras",
            cpf_cnpj="987.654.321-00",
            email="semcompras@test.com",
        )
        url = reverse("customer:customer_detail", kwargs={"pk": novo_cliente.pk})
        response = self.client.get(url)
        self.assertEqual(response.context["total_purchases"], 0)
        self.assertEqual(response.context["total_spent"], Decimal("0.00"))
        self.assertEqual(response.context["monthly_average"], Decimal("0.00"))

    def test_redireciona_usuario_nao_autenticado(self):
        self.client.logout()
        url = reverse("customer:customer_detail", kwargs={"pk": self.customer.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
