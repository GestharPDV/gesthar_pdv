from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from user.models import UserGesthar
from .models import CashRegister, Sale, SalePayment


class SalesReportAccessTest(TestCase):
    def setUp(self):
        self.admin = UserGesthar.objects.create_user(
            email="admin@test.com",
            password="testpass123",
            role="ADMIN",
            cpf="111.111.111-11",
        )
        self.vendedor = UserGesthar.objects.create_user(
            email="vendedor@test.com",
            password="testpass123",
            role="VENDEDOR",
            cpf="222.222.222-22",
        )
        self.url = reverse("sales:report-sales")

    def test_vendedor_nao_pode_acessar(self):
        """Usuário VENDEDOR deve ser bloqueado (redirect para home)."""
        self.client.force_login(self.vendedor)
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_admin_acessa_com_200(self):
        """Usuário ADMIN deve receber HTTP 200."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_contexto_contem_chaves_obrigatorias(self):
        """Contexto da view deve conter as chaves de gráficos e totalizações."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertIn("payment_chart_json", response.context)
        self.assertIn("user_chart_json", response.context)
        self.assertIn("total_revenue", response.context)
        self.assertIn("total_discounts", response.context)
        self.assertIn("completed_sales_count", response.context)


class SalesReportTotalizationTest(TestCase):
    def setUp(self):
        self.admin = UserGesthar.objects.create_user(
            email="admin2@test.com",
            password="testpass123",
            role="ADMIN",
            cpf="333.333.333-33",
        )
        self.url = reverse("sales:report-sales")

        cash_register = CashRegister.objects.create(
            user=self.admin,
            opening_balance=Decimal("0.00"),
            status=CashRegister.Status.OPEN,
        )

        sale = Sale.objects.create(
            user=self.admin,
            cash_register_session=cash_register,
            status=Sale.Status.DRAFT,
            gross_amount=Decimal("200.00"),
            discount_amount=Decimal("10.00"),
            net_amount=Decimal("190.00"),
        )
        # Força o status COMPLETED e define completed_at sem passar pelo fluxo completo
        Sale.objects.filter(pk=sale.pk).update(
            status=Sale.Status.COMPLETED,
            completed_at=timezone.now(),
        )
        # Cria pagamento via bulk_create para contornar a validação de status
        SalePayment.objects.bulk_create([
            SalePayment(sale=sale, method="PIX", amount=Decimal("190.00")),
        ])

    def test_faturamento_total_corresponde_ao_net_amount(self):
        """total_revenue deve somar net_amount das vendas COMPLETED no período."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.context["total_revenue"], Decimal("190.00"))

    def test_total_descontos_corresponde_ao_discount_amount(self):
        """total_discounts deve somar discount_amount das vendas COMPLETED no período."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.context["total_discounts"], Decimal("10.00"))

    def test_contagem_de_vendas_concluidas(self):
        """completed_sales_count deve refletir o número correto de vendas."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.context["completed_sales_count"], 1)

    def test_payment_chart_json_contem_dados(self):
        """payment_chart_json deve ser JSON válido com labels e values."""
        import json
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        data = json.loads(response.context["payment_chart_json"])
        self.assertIn("labels", data)
        self.assertIn("values", data)
        self.assertEqual(data["labels"], ["PIX"])
        self.assertAlmostEqual(data["values"][0], 190.0)
