import json
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from product.models import Category, Color, Size, Product, ProductVariation
from sales.models import CashRegister, Sale, SaleItem, SalePayment

User = get_user_model()


class SaleDiscountTestCase(TestCase):
    """Testa que o desconto é corretamente aplicado do frontend ao backend."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='caixa@teste.com', password='senha123')
        self.client.login(username='caixa@teste.com', password='senha123')

        self.session = CashRegister.objects.create(
            user=self.user,
            opening_balance=Decimal('100.00'),
            status=CashRegister.Status.OPEN,
        )

        category = Category.objects.create(name='Roupas')
        color = Color.objects.create(name='Preto')
        size = Size.objects.create(name='M')
        product = Product.objects.create(
            name='Camiseta',
            selling_price=Decimal('100.00'),
            category=category,
        )
        self.variation = ProductVariation.objects.create(
            product=product,
            color=color,
            size=size,
            stock=50,
            minimum_stock=5,
        )

        self.sale = Sale.objects.create(
            user=self.user,
            cash_register_session=self.session,
            status=Sale.Status.DRAFT,
        )
        SaleItem.objects.create(
            sale=self.sale,
            variation=self.variation,
            quantity=2,
            unit_price=Decimal('100.00'),
        )
        self.sale.calculate_totals()
        self.sale.refresh_from_db()

    # --- Testes de modelo ---

    def test_gross_amount_calculado_corretamente(self):
        """gross_amount deve ser a soma dos itens sem desconto global."""
        self.assertEqual(self.sale.gross_amount, Decimal('200.00'))

    def test_net_amount_sem_desconto(self):
        """net_amount sem desconto deve igualar gross_amount."""
        self.assertEqual(self.sale.net_amount, Decimal('200.00'))

    def test_net_amount_com_desconto_absoluto(self):
        """net_amount deve ser gross_amount – discount_amount."""
        self.sale.discount_amount = Decimal('30.00')
        self.sale.save(update_fields=['discount_amount'])
        self.sale.calculate_totals()
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.net_amount, Decimal('170.00'))

    def test_desconto_nao_pode_ser_negativo_no_modelo(self):
        """net_amount nunca pode ficar negativo."""
        self.sale.discount_amount = Decimal('300.00')
        self.sale.save(update_fields=['discount_amount'])
        self.sale.calculate_totals()
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.net_amount, Decimal('0.00'))

    def test_remaining_balance_com_desconto(self):
        """remaining_balance deve refletir o desconto aplicado."""
        self.sale.discount_amount = Decimal('50.00')
        self.sale.save(update_fields=['discount_amount'])
        self.sale.calculate_totals()
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.remaining_balance, Decimal('150.00'))

    # --- Testes de view (apply_discount_view) ---

    def test_apply_discount_view_ajax_sucesso(self):
        """POST AJAX em apply-discount retorna JSON com net_amount correto."""
        url = reverse('sales:apply-discount')
        response = self.client.post(
            url,
            data={'discount_amount': '50.00'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertAlmostEqual(data['net_amount'], 150.00, places=2)
        self.assertAlmostEqual(data['remaining_balance'], 150.00, places=2)

    def test_apply_discount_view_ajax_desconto_negativo(self):
        """Desconto negativo deve retornar 400."""
        url = reverse('sales:apply-discount')
        response = self.client.post(
            url,
            data={'discount_amount': '-10.00'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_apply_discount_view_ajax_desconto_maior_que_total(self):
        """Desconto maior que gross_amount deve retornar 400."""
        url = reverse('sales:apply-discount')
        response = self.client.post(
            url,
            data={'discount_amount': '999.00'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)

    def test_apply_discount_view_persiste_no_banco(self):
        """O desconto enviado deve ser persistido no banco com Decimal."""
        url = reverse('sales:apply-discount')
        self.client.post(
            url,
            data={'discount_amount': '25.00'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.discount_amount, Decimal('25.00'))
        self.assertEqual(self.sale.net_amount, Decimal('175.00'))

    # --- Teste de fluxo completo ---

    def test_fluxo_completo_venda_com_desconto(self):
        """Simula o fluxo completo: aplicar desconto → pagar → concluir venda."""
        # 1. Aplica desconto de R$ 20
        self.client.post(
            reverse('sales:apply-discount'),
            data={'discount_amount': '20.00'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.net_amount, Decimal('180.00'))

        # 2. Adiciona pagamento pelo valor líquido (com desconto)
        self.client.post(
            reverse('sales:add-payment'),
            data={'method': 'DINHEIRO', 'amount': '180.00'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.sale.refresh_from_db()
        self.assertTrue(self.sale.is_fully_paid)

        # 3. Conclui a venda
        self.client.post(reverse('sales:complete-sale', kwargs={'sale_id': self.sale.pk}))
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status, Sale.Status.COMPLETED)

        # 4. Valida valores finais
        self.assertEqual(self.sale.net_amount, Decimal('180.00'))
        self.assertEqual(self.sale.discount_amount, Decimal('20.00'))
        self.assertEqual(self.sale.total_paid, Decimal('180.00'))
        self.assertEqual(self.sale.change_amount, Decimal('0.00'))

    def test_pagamento_com_valor_cheio_nao_conclui_venda_com_desconto(self):
        """
        Se o frontend ignorar o desconto e pagar o valor cheio,
        a venda ainda deve ser concluída (pagou a mais → troco).
        Mas o net_amount salvo deve ser o valor COM desconto.
        """
        self.client.post(
            reverse('sales:apply-discount'),
            data={'discount_amount': '50.00'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.net_amount, Decimal('150.00'))

        # Paga o valor bruto (sem saber do desconto)
        self.client.post(
            reverse('sales:add-payment'),
            data={'method': 'DINHEIRO', 'amount': '200.00'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.sale.refresh_from_db()

        self.client.post(reverse('sales:complete-sale', kwargs={'sale_id': self.sale.pk}))
        self.sale.refresh_from_db()

        self.assertEqual(self.sale.status, Sale.Status.COMPLETED)
        # Troco = 200 - 150 = 50
        self.assertEqual(self.sale.change_amount, Decimal('50.00'))
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
