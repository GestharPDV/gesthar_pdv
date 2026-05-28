"""
Testes do app sales.

Inclui:
  - SaleDiscountTestCase        – desconto e fluxo de venda
  - SalesReportAccessTest       – acesso ao relatório de vendas
  - SalesReportTotalizationTest – totalizações do relatório de vendas
  - BaseFinancialTestCase       – fixtures compartilhadas do dashboard financeiro
  - GetFinancialIndicatorsTest  – services.get_financial_indicators
  - GetAverageTicketTest        – services.get_average_ticket
  - GetABCCurveTest             – services.get_abc_curve
  - GetSalesEvolutionTest       – services.get_sales_evolution
  - GetCapitalImobilizadoTest   – services.get_capital_imobilizado
  - GetGmroiTest                – services.get_gmroi
  - GetStockCoverageAndTurnoverTest – services.get_stock_coverage_and_turnover
  - GetBulkStockCoverageTest    – services.get_bulk_stock_coverage
  - GetStockoutRiskListTest     – services.get_stockout_risk_list
  - ReportFinancialViewTest     – ReportFinancialView

Estrutura de dados de referência (dashboard financeiro)
--------------------------------------------------------
Sale 1 (PIX):      2× Camiseta @ R$100  → gross=200, discount=20, net=180
                   Custo fornecedor = R$60/un → CMV item = 120
Sale 2 (Dinheiro): 2× Calça    @ R$ 50  → gross=100, discount=10, net= 90
                   Custo fornecedor = R$20/un → CMV item =  40

Totalizadores esperados
  gross_revenue   = 300     net_revenue    = 270   total_discounts = 30
  cmv             = 160     gross_profit   = 110   profit_margin   ≈ 40.74 %
  avg_ticket      = 135     capital_imobil = 700   gmroi           ≈ 0.1571
  stock cob. A    = 150d    stock cob. B   = 75d
"""

import json
from datetime import date, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from product.models import (
    Category, Color, Size, Supplier,
    Product, ProductVariation, ProductSupplier,
)
from user.models import UserGesthar
from sales.models import CashRegister, Sale, SaleItem, SalePayment
from sales import services

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Desconto e fluxo de venda
# ─────────────────────────────────────────────────────────────────────────────

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
        self.client.post(
            reverse('sales:apply-discount'),
            data={'discount_amount': '20.00'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.net_amount, Decimal('180.00'))

        self.client.post(
            reverse('sales:add-payment'),
            data={'method': 'DINHEIRO', 'amount': '180.00'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.sale.refresh_from_db()
        self.assertTrue(self.sale.is_fully_paid)

        self.client.post(reverse('sales:complete-sale', kwargs={'sale_id': self.sale.pk}))
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status, Sale.Status.COMPLETED)

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

        self.client.post(
            reverse('sales:add-payment'),
            data={'method': 'DINHEIRO', 'amount': '200.00'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.sale.refresh_from_db()

        self.client.post(reverse('sales:complete-sale', kwargs={'sale_id': self.sale.pk}))
        self.sale.refresh_from_db()

        self.assertEqual(self.sale.status, Sale.Status.COMPLETED)
        self.assertEqual(self.sale.change_amount, Decimal('50.00'))


# ─────────────────────────────────────────────────────────────────────────────
# Relatório de vendas (acesso e totalizações)
# ─────────────────────────────────────────────────────────────────────────────

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
        Sale.objects.filter(pk=sale.pk).update(
            status=Sale.Status.COMPLETED,
            completed_at=timezone.now(),
        )
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
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        data = json.loads(response.context["payment_chart_json"])
        self.assertIn("labels", data)
        self.assertIn("values", data)
        self.assertEqual(data["labels"], ["PIX"])
        self.assertAlmostEqual(data["values"][0], 190.0)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures compartilhadas – Dashboard Financeiro
# ─────────────────────────────────────────────────────────────────────────────

class BaseFinancialTestCase(TestCase):
    """
    Cria dois produtos com custos de fornecedor conhecidos e duas vendas
    concluídas hoje, de modo que todos os cálculos possam ser verificados
    deterministicamente.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.admin = UserGesthar.objects.create_user(
            email="admin@fin.test",
            password="pass123",
            role="ADMIN",
            cpf="111.111.111-11",
        )
        cls.vendedor = UserGesthar.objects.create_user(
            email="vendedor@fin.test",
            password="pass123",
            role="VENDEDOR",
            cpf="222.222.222-22",
        )

        category = Category.objects.create(name="Vestuário")
        color    = Color.objects.create(name="Preto")
        size_m   = Size.objects.create(name="M")
        size_g   = Size.objects.create(name="G")
        supplier = Supplier.objects.create(name="Fornecedor Teste")

        # Produto A: Camiseta — stock=10, supplier_cost=60 → R$600 no capital imobilizado
        cls.product_a = Product.objects.create(
            name="Camiseta",
            selling_price=Decimal("100.00"),
            category=category,
        )
        cls.var_a = ProductVariation.objects.create(
            product=cls.product_a, color=color, size=size_m, stock=10,
        )
        ProductSupplier.objects.create(
            product=cls.product_a, supplier=supplier, cost_price=Decimal("60.00"),
        )

        # Produto B: Calça — stock=5, supplier_cost=20 → R$100 no capital imobilizado
        cls.product_b = Product.objects.create(
            name="Calça",
            selling_price=Decimal("50.00"),
            category=category,
        )
        cls.var_b = ProductVariation.objects.create(
            product=cls.product_b, color=color, size=size_g, stock=5,
        )
        ProductSupplier.objects.create(
            product=cls.product_b, supplier=supplier, cost_price=Decimal("20.00"),
        )

        cash_register = CashRegister.objects.create(
            user=cls.admin,
            opening_balance=Decimal("0.00"),
            status=CashRegister.Status.OPEN,
        )

        # Venda 1: 2× Camiseta, desconto 20, net 180, PIX
        cls.sale_1 = Sale.objects.create(
            user=cls.admin,
            cash_register_session=cash_register,
            status=Sale.Status.DRAFT,
            discount_amount=Decimal("20.00"),
        )
        SaleItem.objects.create(
            sale=cls.sale_1, variation=cls.var_a, quantity=2, unit_price=Decimal("100.00"),
        )
        cls.sale_1.refresh_from_db()
        Sale.objects.filter(pk=cls.sale_1.pk).update(
            status=Sale.Status.COMPLETED, completed_at=timezone.now(),
        )
        SalePayment.objects.bulk_create([
            SalePayment(sale=cls.sale_1, method="PIX", amount=Decimal("180.00")),
        ])

        # Venda 2: 2× Calça, desconto 10, net 90, Dinheiro
        cls.sale_2 = Sale.objects.create(
            user=cls.admin,
            cash_register_session=cash_register,
            status=Sale.Status.DRAFT,
            discount_amount=Decimal("10.00"),
        )
        SaleItem.objects.create(
            sale=cls.sale_2, variation=cls.var_b, quantity=2, unit_price=Decimal("50.00"),
        )
        cls.sale_2.refresh_from_db()
        Sale.objects.filter(pk=cls.sale_2.pk).update(
            status=Sale.Status.COMPLETED, completed_at=timezone.now(),
        )
        SalePayment.objects.bulk_create([
            SalePayment(sale=cls.sale_2, method="DINHEIRO", amount=Decimal("90.00")),
        ])

        cls.today     = date.today()
        cls.yesterday = cls.today - timedelta(days=1)


# ─────────────────────────────────────────────────────────────────────────────
# 1. get_financial_indicators
# ─────────────────────────────────────────────────────────────────────────────

class GetFinancialIndicatorsTest(BaseFinancialTestCase):

    def _indicators(self):
        return services.get_financial_indicators(self.today, self.today)

    def test_receita_bruta_soma_gross_amount_das_vendas_concluidas(self):
        """gross_revenue = 200 (sale_1) + 100 (sale_2) = 300"""
        self.assertEqual(self._indicators()["gross_revenue"], Decimal("300.00"))

    def test_receita_liquida_soma_net_amount_das_vendas_concluidas(self):
        """net_revenue = 180 + 90 = 270"""
        self.assertEqual(self._indicators()["net_revenue"], Decimal("270.00"))

    def test_total_descontos_soma_discount_amount(self):
        """total_discounts = 20 + 10 = 30"""
        self.assertEqual(self._indicators()["total_discounts"], Decimal("30.00"))

    def test_cmv_calculado_pelo_custo_medio_do_fornecedor(self):
        """CMV = (60 × 2) + (20 × 2) = 120 + 40 = 160"""
        self.assertEqual(self._indicators()["cmv"], Decimal("160.00"))

    def test_lucro_bruto_e_receita_liquida_menos_cmv(self):
        """gross_profit = 270 – 160 = 110"""
        self.assertEqual(self._indicators()["gross_profit"], Decimal("110.00"))

    def test_margem_de_lucro_percentual_correto(self):
        """profit_margin = 110 / 270 × 100 ≈ 40.74 %"""
        expected = Decimal("110") / Decimal("270") * 100
        self.assertAlmostEqual(
            float(self._indicators()["profit_margin"]),
            float(expected),
            places=4,
        )

    def test_periodo_sem_vendas_retorna_zeros(self):
        result = services.get_financial_indicators(self.yesterday, self.yesterday)
        self.assertEqual(result["gross_revenue"], Decimal("0"))
        self.assertEqual(result["net_revenue"],   Decimal("0"))
        self.assertEqual(result["cmv"],           Decimal("0"))
        self.assertEqual(result["gross_profit"],  Decimal("0"))
        self.assertEqual(result["profit_margin"], Decimal("0"))

    def test_vendas_fora_do_periodo_sao_excluidas(self):
        """Uma venda completada há 40 dias não deve entrar no relatório de hoje."""
        old_sale = Sale.objects.create(
            user=self.admin,
            gross_amount=Decimal("500.00"),
            net_amount=Decimal("500.00"),
        )
        Sale.objects.filter(pk=old_sale.pk).update(
            status=Sale.Status.COMPLETED,
            completed_at=timezone.now() - timedelta(days=40),
        )
        result = services.get_financial_indicators(self.today, self.today)
        self.assertEqual(result["gross_revenue"], Decimal("300.00"))

    def test_vendas_em_rascunho_nao_contam(self):
        draft = Sale.objects.create(
            user=self.admin,
            gross_amount=Decimal("999.00"),
            net_amount=Decimal("999.00"),
            status=Sale.Status.DRAFT,
        )
        result = services.get_financial_indicators(self.today, self.today)
        self.assertEqual(result["gross_revenue"], Decimal("300.00"))
        draft.delete()

    def test_produto_sem_fornecedor_tem_cmv_zero(self):
        """Se o produto não tem fornecedor cadastrado, seu CMV deve ser zero."""
        category = Category.objects.first()
        color = Color.objects.first()
        size = Size.objects.create(name="PP")
        product_c = Product.objects.create(
            name="Sem Custo", selling_price=Decimal("80.00"), category=category,
        )
        var_c = ProductVariation.objects.create(
            product=product_c, color=color, size=size, stock=5,
        )
        cash = CashRegister.objects.create(
            user=self.admin, opening_balance=Decimal("0"), status=CashRegister.Status.OPEN,
        )
        sale_c = Sale.objects.create(
            user=self.admin, cash_register_session=cash, status=Sale.Status.DRAFT,
        )
        SaleItem.objects.create(sale=sale_c, variation=var_c, quantity=1, unit_price=Decimal("80.00"))
        Sale.objects.filter(pk=sale_c.pk).update(
            status=Sale.Status.COMPLETED, completed_at=timezone.now(),
        )
        result = services.get_financial_indicators(self.today, self.today)
        # CMV do produto C = 0; total CMV deve aumentar apenas pelos produtos A e B
        self.assertEqual(result["cmv"], Decimal("160.00"))


# ─────────────────────────────────────────────────────────────────────────────
# 2. get_average_ticket
# ─────────────────────────────────────────────────────────────────────────────

class GetAverageTicketTest(BaseFinancialTestCase):

    def test_ticket_medio_e_receita_liquida_dividida_por_quantidade(self):
        """avg_ticket = 270 / 2 = 135"""
        result = services.get_average_ticket(self.today, self.today)
        self.assertEqual(result, Decimal("135"))

    def test_sem_vendas_no_periodo_retorna_zero(self):
        result = services.get_average_ticket(self.yesterday, self.yesterday)
        self.assertEqual(result, Decimal("0"))

    def test_uma_venda_ticket_igual_ao_net_amount(self):
        """Com uma única venda, ticket médio = net_amount da venda."""
        result = services.get_average_ticket(self.today, self.today)
        self.assertAlmostEqual(float(result), 135.0, places=2)


# ─────────────────────────────────────────────────────────────────────────────
# 3. get_abc_curve
# ─────────────────────────────────────────────────────────────────────────────

class GetABCCurveTest(BaseFinancialTestCase):

    def _curve(self):
        return list(services.get_abc_curve(self.today, self.today))

    def test_retorna_dois_produtos_vendidos_hoje(self):
        self.assertEqual(len(self._curve()), 2)

    def test_ordenado_por_faturamento_decrescente(self):
        """Camiseta (R$200) deve vir antes de Calça (R$100)."""
        items = self._curve()
        self.assertEqual(items[0]["variation__product__name"], "Camiseta")
        self.assertEqual(items[1]["variation__product__name"], "Calça")

    def test_faturamento_do_primeiro_produto_correto(self):
        """total_revenue da Camiseta = 2 × 100 = 200"""
        self.assertEqual(self._curve()[0]["total_revenue"], Decimal("200.00"))

    def test_custo_medio_do_fornecedor_incluido(self):
        """avg_unit_cost deve refletir o custo do fornecedor cadastrado."""
        items = self._curve()
        self.assertAlmostEqual(float(items[0]["avg_unit_cost"]), 60.0, places=2)
        self.assertAlmostEqual(float(items[1]["avg_unit_cost"]), 20.0, places=2)

    def test_produto_sem_fornecedor_tem_avg_unit_cost_zero(self):
        """Produto sem ProductSupplier → avg_unit_cost deve ser Coalesce para 0."""
        category = Category.objects.first()
        color = Color.objects.first()
        size = Size.objects.create(name="XG")
        p_sem_custo = Product.objects.create(
            name="Sem Fornecedor", selling_price=Decimal("50.00"), category=category,
        )
        var = ProductVariation.objects.create(product=p_sem_custo, color=color, size=size, stock=3)
        cash = CashRegister.objects.create(
            user=self.admin, opening_balance=0, status=CashRegister.Status.OPEN,
        )
        sale = Sale.objects.create(user=self.admin, cash_register_session=cash, status=Sale.Status.DRAFT)
        SaleItem.objects.create(sale=sale, variation=var, quantity=1, unit_price=Decimal("50.00"))
        Sale.objects.filter(pk=sale.pk).update(
            status=Sale.Status.COMPLETED, completed_at=timezone.now(),
        )
        items = list(services.get_abc_curve(self.today, self.today))
        sem_custo = next(i for i in items if i["variation__product__name"] == "Sem Fornecedor")
        self.assertEqual(sem_custo["avg_unit_cost"], Decimal("0"))

    def test_sem_vendas_retorna_queryset_vazio(self):
        items = list(services.get_abc_curve(self.yesterday, self.yesterday))
        self.assertEqual(items, [])


# ─────────────────────────────────────────────────────────────────────────────
# 4. get_sales_evolution
# ─────────────────────────────────────────────────────────────────────────────

class GetSalesEvolutionTest(BaseFinancialTestCase):

    def _evolution(self):
        return list(services.get_sales_evolution(self.today, self.today))

    def test_agrupa_ambas_as_vendas_no_mesmo_dia(self):
        """Duas vendas hoje → uma única linha na evolução."""
        self.assertEqual(len(self._evolution()), 1)

    def test_receita_diaria_e_soma_dos_net_amounts(self):
        """daily_revenue = 180 + 90 = 270"""
        self.assertEqual(self._evolution()[0]["daily_revenue"], Decimal("270.00"))

    def test_contagem_de_vendas_no_dia_correta(self):
        """sale_count = 2"""
        self.assertEqual(self._evolution()[0]["sale_count"], 2)

    def test_sem_vendas_retorna_lista_vazia(self):
        result = list(services.get_sales_evolution(self.yesterday, self.yesterday))
        self.assertEqual(result, [])

    def test_vendas_em_dias_distintos_geram_linhas_separadas(self):
        """Uma venda de ontem mais duas de hoje → duas linhas na evolução."""
        cash = CashRegister.objects.create(
            user=self.admin, opening_balance=0, status=CashRegister.Status.OPEN,
        )
        old_sale = Sale.objects.create(
            user=self.admin, cash_register_session=cash,
            gross_amount=Decimal("50.00"), net_amount=Decimal("50.00"),
        )
        Sale.objects.filter(pk=old_sale.pk).update(
            status=Sale.Status.COMPLETED,
            completed_at=timezone.now() - timedelta(days=1),
        )
        result = list(services.get_sales_evolution(self.yesterday, self.today))
        self.assertEqual(len(result), 2)


# ─────────────────────────────────────────────────────────────────────────────
# 5. get_capital_imobilizado
# ─────────────────────────────────────────────────────────────────────────────

class GetCapitalImobilizadoTest(TestCase):
    """Usa seu próprio setUp para controlar o estoque com precisão."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        category = Category.objects.create(name="Cat Capital")
        cls.color = Color.objects.create(name="Branco")
        cls.size = Size.objects.create(name="U")
        cls.supplier = Supplier.objects.create(name="Forn Capital")

        cls.product_x = Product.objects.create(
            name="Produto X", selling_price=Decimal("100.00"), category=category,
        )
        cls.var_x = ProductVariation.objects.create(
            product=cls.product_x, color=cls.color, size=cls.size, stock=10,
        )
        ProductSupplier.objects.create(
            product=cls.product_x, supplier=cls.supplier, cost_price=Decimal("50.00"),
        )

    def test_multiplica_estoque_por_custo_medio_do_fornecedor(self):
        """10 unidades × R$50 = R$500"""
        result = services.get_capital_imobilizado()
        self.assertAlmostEqual(float(result), 500.0, places=2)

    def test_produto_sem_fornecedor_tem_contribuicao_zero(self):
        """Produto sem ProductSupplier contribui R$0 ao capital imobilizado."""
        category = Category.objects.first()
        size2 = Size.objects.create(name="U2")
        product_sem = Product.objects.create(
            name="Sem Custo Capital", selling_price=Decimal("80.00"), category=category,
        )
        ProductVariation.objects.create(
            product=product_sem, color=self.color, size=size2, stock=20,
        )
        result = services.get_capital_imobilizado()
        self.assertAlmostEqual(float(result), 500.0, places=2)

    def test_variacao_inativa_nao_contabilizada(self):
        """Variação com is_active=False não entra no cálculo."""
        size3 = Size.objects.create(name="U3")
        ProductVariation.objects.create(
            product=self.product_x, color=self.color, size=size3, stock=100, is_active=False,
        )
        result = services.get_capital_imobilizado()
        self.assertAlmostEqual(float(result), 500.0, places=2)

    def test_produto_inativo_nao_contabilizado(self):
        """Produto com is_active=False não entra no cálculo."""
        category = Category.objects.first()
        size4 = Size.objects.create(name="U4")
        product_off = Product.objects.create(
            name="Produto Off", selling_price=Decimal("200.00"), category=category, is_active=False,
        )
        var_off = ProductVariation.objects.create(
            product=product_off, color=self.color, size=size4, stock=50,
        )
        ProductSupplier.objects.create(
            product=product_off, supplier=self.supplier, cost_price=Decimal("100.00"),
        )
        result = services.get_capital_imobilizado()
        self.assertAlmostEqual(float(result), 500.0, places=2)

    def test_sem_nenhum_estoque_retorna_zero(self):
        """Variação com stock=0 não altera o total."""
        ProductVariation.objects.filter(pk=self.var_x.pk).update(stock=0)
        result = services.get_capital_imobilizado()
        self.assertAlmostEqual(float(result), 0.0, places=2)


# ─────────────────────────────────────────────────────────────────────────────
# 6. get_gmroi
# ─────────────────────────────────────────────────────────────────────────────

class GetGmroiTest(BaseFinancialTestCase):

    def test_gmroi_calculado_corretamente(self):
        """
        gross_margin = net_revenue(270) – COGS(160) = 110
        capital_imobilizado = 700
        gmroi = 110 / 700 ≈ 0.1571
        """
        result = services.get_gmroi(self.today, self.today)
        self.assertAlmostEqual(float(result), 110 / 700, places=4)

    def test_gmroi_zero_quando_sem_vendas_no_periodo(self):
        """Sem vendas → gross_margin = 0, GMROI deve ser 0 (não dividir por zero)."""
        result = services.get_gmroi(self.yesterday, self.yesterday)
        self.assertEqual(result, Decimal("0"))

    def test_gmroi_zero_quando_capital_imobilizado_e_zero(self):
        """Se o capital imobilizado for 0 (sem custos), evita divisão por zero."""
        ProductSupplier.objects.all().delete()
        result = services.get_gmroi(self.today, self.today)
        self.assertEqual(result, Decimal("0"))

    def test_margem_bruta_usada_no_gmroi_e_receita_menos_cogs(self):
        """Verifica a equação: gross_margin = net_revenue – COGS"""
        indicators = services.get_financial_indicators(self.today, self.today)
        expected_margin = indicators["net_revenue"] - indicators["cmv"]
        capital = services.get_capital_imobilizado()
        expected_gmroi = expected_margin / capital if capital > 0 else Decimal("0")
        result = services.get_gmroi(self.today, self.today)
        self.assertAlmostEqual(float(result), float(expected_gmroi), places=6)


# ─────────────────────────────────────────────────────────────────────────────
# 7. get_stock_coverage_and_turnover
# ─────────────────────────────────────────────────────────────────────────────

class GetStockCoverageAndTurnoverTest(BaseFinancialTestCase):

    def test_estoque_atual_do_produto_a_correto(self):
        result = services.get_stock_coverage_and_turnover(self.product_a.pk, 30)
        self.assertEqual(result["current_stock"], 10)

    def test_estoque_atual_do_produto_b_correto(self):
        result = services.get_stock_coverage_and_turnover(self.product_b.pk, 30)
        self.assertEqual(result["current_stock"], 5)

    def test_media_diaria_de_vendas_produto_a(self):
        """avg_daily = round(2 / 30, 2) = 0.07 (service rounds to 2 decimal places)"""
        result = services.get_stock_coverage_and_turnover(self.product_a.pk, 30)
        self.assertAlmostEqual(result["avg_daily_sales"], round(2 / 30, 2), places=2)

    def test_cobertura_em_dias_produto_a(self):
        """coverage = int(10 / (2/30)) = int(150) = 150"""
        result = services.get_stock_coverage_and_turnover(self.product_a.pk, 30)
        self.assertEqual(result["days_coverage"], 150)

    def test_cobertura_em_dias_produto_b(self):
        """coverage = int(5 / (2/30)) = int(75) = 75"""
        result = services.get_stock_coverage_and_turnover(self.product_b.pk, 30)
        self.assertEqual(result["days_coverage"], 75)

    def test_sem_vendas_retorna_cobertura_none(self):
        """Produto sem vendas no período → days_coverage=None (cobertura infinita)."""
        category = Category.objects.first()
        color = Color.objects.first()
        size = Size.objects.create(name="SV")
        p_sem_venda = Product.objects.create(
            name="Sem Venda", selling_price=Decimal("10.00"), category=category,
        )
        ProductVariation.objects.create(product=p_sem_venda, color=color, size=size, stock=50)
        result = services.get_stock_coverage_and_turnover(p_sem_venda.pk, 30)
        self.assertIsNone(result["days_coverage"])
        self.assertEqual(result["current_stock"], 50)


# ─────────────────────────────────────────────────────────────────────────────
# 8. get_bulk_stock_coverage
# ─────────────────────────────────────────────────────────────────────────────

class GetBulkStockCoverageTest(BaseFinancialTestCase):

    def _bulk(self):
        return services.get_bulk_stock_coverage(
            [self.product_a.pk, self.product_b.pk], days_analyzed=30,
        )

    def test_retorna_entrada_para_ambos_os_produtos(self):
        result = self._bulk()
        self.assertIn(self.product_a.pk, result)
        self.assertIn(self.product_b.pk, result)

    def test_cobertura_produto_a_em_lote(self):
        self.assertEqual(self._bulk()[self.product_a.pk]["days_coverage"], 150)

    def test_cobertura_produto_b_em_lote(self):
        self.assertEqual(self._bulk()[self.product_b.pk]["days_coverage"], 75)

    def test_estoque_atual_correto_em_lote(self):
        result = self._bulk()
        self.assertEqual(result[self.product_a.pk]["current_stock"], 10)
        self.assertEqual(result[self.product_b.pk]["current_stock"], 5)

    def test_produto_sem_vendas_tem_cobertura_none_em_lote(self):
        category = Category.objects.first()
        color = Color.objects.first()
        size = Size.objects.create(name="BK")
        p_novo = Product.objects.create(
            name="Novo sem venda", selling_price=Decimal("30.00"), category=category,
        )
        ProductVariation.objects.create(product=p_novo, color=color, size=size, stock=20)
        result = services.get_bulk_stock_coverage([p_novo.pk], days_analyzed=30)
        self.assertIsNone(result[p_novo.pk]["days_coverage"])


# ─────────────────────────────────────────────────────────────────────────────
# 9. get_stockout_risk_list
# ─────────────────────────────────────────────────────────────────────────────

class GetStockoutRiskListTest(TestCase):
    """
    Dados específicos para testar os alertas de ruptura:

    Meia (crítica):  stock=1,   vendeu 20 un/30d → cobertura≈1d  < 7 ⚠
    Cueca (crítica): stock=3,   vendeu 20 un/30d → cobertura≈4d  < 7 ⚠
    Blusa (segura):  stock=100, vendeu  1 un/30d → cobertura≈3000d > 7 ✓
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.admin = UserGesthar.objects.create_user(
            email="admin@stockout.test",
            password="pass123",
            role="ADMIN",
            cpf="333.333.333-33",
        )
        category = Category.objects.create(name="Cat Ruptura")
        color    = Color.objects.create(name="Verde")
        supplier = Supplier.objects.create(name="Forn Ruptura")
        cash     = CashRegister.objects.create(
            user=cls.admin, opening_balance=0, status=CashRegister.Status.OPEN,
        )

        def _make_product(name, stock, sold_qty):
            prod = Product.objects.create(
                name=name, selling_price=Decimal("10.00"), category=category,
            )
            size_local = Size.objects.create(name=f"Sz-{name}")
            var = ProductVariation.objects.create(
                product=prod, color=color, size=size_local, stock=stock,
            )
            ProductSupplier.objects.create(
                product=prod, supplier=supplier, cost_price=Decimal("5.00"),
            )
            sale = Sale.objects.create(
                user=cls.admin, cash_register_session=cash, status=Sale.Status.DRAFT,
            )
            SaleItem.objects.create(
                sale=sale, variation=var, quantity=sold_qty, unit_price=Decimal("10.00"),
            )
            Sale.objects.filter(pk=sale.pk).update(
                status=Sale.Status.COMPLETED, completed_at=timezone.now(),
            )
            return prod, var

        cls.product_meia,  cls.var_meia  = _make_product("Meia",  stock=1,   sold_qty=20)
        cls.product_cueca, cls.var_cueca = _make_product("Cueca", stock=3,   sold_qty=20)
        cls.product_blusa, cls.var_blusa = _make_product("Blusa", stock=100, sold_qty=1)

    def setUp(self):
        cache.clear()

    def test_produtos_criticos_aparecem_na_lista(self):
        alerts = services.get_stockout_risk_list(days_analyzed=30, coverage_threshold=7)
        names = [a["product_name"] for a in alerts]
        self.assertIn("Meia",  names)
        self.assertIn("Cueca", names)

    def test_produto_com_cobertura_segura_nao_aparece(self):
        alerts = services.get_stockout_risk_list(days_analyzed=30, coverage_threshold=7)
        names = [a["product_name"] for a in alerts]
        self.assertNotIn("Blusa", names)

    def test_lista_ordenada_por_cobertura_crescente(self):
        """Meia (cobertura≈1d) deve aparecer antes de Cueca (cobertura≈4d)."""
        alerts = services.get_stockout_risk_list(days_analyzed=30, coverage_threshold=7)
        names = [a["product_name"] for a in alerts]
        self.assertLess(names.index("Meia"), names.index("Cueca"))

    def test_cobertura_da_meia_e_menor_que_limiar(self):
        alerts = services.get_stockout_risk_list(days_analyzed=30, coverage_threshold=7)
        meia = next(a for a in alerts if a["product_name"] == "Meia")
        self.assertLess(meia["days_coverage"], 7)

    def test_resultado_e_cacheado_apos_primeira_chamada(self):
        cache.clear()
        services.get_stockout_risk_list(days_analyzed=30, coverage_threshold=7)
        self.assertIsNotNone(cache.get("stockout_risk_30_7"))

    def test_segunda_chamada_retorna_dados_do_cache(self):
        result1 = services.get_stockout_risk_list(days_analyzed=30, coverage_threshold=7)
        ProductVariation.objects.filter(pk=self.var_meia.pk).update(stock=9999)
        result2 = services.get_stockout_risk_list(days_analyzed=30, coverage_threshold=7)
        self.assertEqual(result1, result2)

    def test_cache_limpo_reflete_dado_atualizado(self):
        services.get_stockout_risk_list(days_analyzed=30, coverage_threshold=7)
        ProductVariation.objects.filter(pk=self.var_meia.pk).update(stock=9999)
        cache.clear()
        result = services.get_stockout_risk_list(days_analyzed=30, coverage_threshold=7)
        names = [a["product_name"] for a in result]
        self.assertNotIn("Meia", names)


# ─────────────────────────────────────────────────────────────────────────────
# 10. ReportFinancialView (acesso, contexto, valores)
# ─────────────────────────────────────────────────────────────────────────────

class ReportFinancialViewTest(BaseFinancialTestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse("sales:report-financial")

    def test_usuario_nao_autenticado_e_redirecionado(self):
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_vendedor_nao_tem_acesso(self):
        self.client.force_login(self.vendedor)
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_admin_recebe_200(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_contexto_contem_todas_as_chaves_obrigatorias(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        chaves_esperadas = [
            "gross_revenue", "net_revenue", "total_discounts",
            "cmv", "gross_profit", "profit_margin",
            "average_ticket", "gmroi", "capital_imobilizado",
            "stockout_alerts", "abc_curve",
            "payment_methods_json", "sales_evolution_json",
            "start_date", "end_date",
        ]
        for chave in chaves_esperadas:
            self.assertIn(chave, response.context, msg=f"Chave ausente no contexto: {chave}")

    def test_valores_do_contexto_batem_com_calculos_conhecidos(self):
        self.client.force_login(self.admin)
        params = {"start_date": self.today.isoformat(), "end_date": self.today.isoformat()}
        response = self.client.get(self.url, params)
        ctx = response.context

        self.assertEqual(ctx["gross_revenue"],   Decimal("300.00"))
        self.assertEqual(ctx["net_revenue"],     Decimal("270.00"))
        self.assertEqual(ctx["total_discounts"], Decimal("30.00"))
        self.assertEqual(ctx["cmv"],             Decimal("160.00"))
        self.assertEqual(ctx["gross_profit"],    Decimal("110.00"))
        self.assertEqual(ctx["average_ticket"],  Decimal("135"))
        self.assertAlmostEqual(float(ctx["profit_margin"]), 40.74, places=1)
        self.assertAlmostEqual(float(ctx["gmroi"]), 110 / 700, places=4)
        self.assertAlmostEqual(float(ctx["capital_imobilizado"]), 700.0, places=2)

    def test_curva_abc_no_contexto_tem_dois_produtos(self):
        self.client.force_login(self.admin)
        params = {"start_date": self.today.isoformat(), "end_date": self.today.isoformat()}
        response = self.client.get(self.url, params)
        self.assertEqual(len(response.context["abc_curve"]), 2)

    def test_curva_abc_inclui_dias_de_cobertura(self):
        self.client.force_login(self.admin)
        params = {"start_date": self.today.isoformat(), "end_date": self.today.isoformat()}
        response = self.client.get(self.url, params)
        for item in response.context["abc_curve"]:
            self.assertIn("days_coverage", item)

    def test_payment_methods_json_contem_pix_e_dinheiro(self):
        self.client.force_login(self.admin)
        params = {"start_date": self.today.isoformat(), "end_date": self.today.isoformat()}
        response = self.client.get(self.url, params)
        data = json.loads(response.context["payment_methods_json"])
        self.assertIn("PIX",      data["labels"])
        self.assertIn("Dinheiro", data["labels"])

    def test_sales_evolution_json_valido_e_contem_receita_do_dia(self):
        self.client.force_login(self.admin)
        params = {"start_date": self.today.isoformat(), "end_date": self.today.isoformat()}
        response = self.client.get(self.url, params)
        data = json.loads(response.context["sales_evolution_json"])
        self.assertEqual(len(data["labels"]), 1)
        self.assertAlmostEqual(data["values"][0], 270.0, places=2)

    def test_datas_invalidas_retornam_date_error_no_contexto(self):
        """end_date < start_date deve popular 'date_error' e retornar HTTP 200."""
        self.client.force_login(self.admin)
        params = {"start_date": self.today.isoformat(), "end_date": self.yesterday.isoformat()}
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        self.assertIn("date_error", response.context)
        self.assertIsNotNone(response.context["date_error"])

    def test_periodo_sem_vendas_zera_indicadores(self):
        """Filtrando por ontem (sem vendas) → receitas e cmv devem ser zero."""
        self.client.force_login(self.admin)
        params = {"start_date": self.yesterday.isoformat(), "end_date": self.yesterday.isoformat()}
        response = self.client.get(self.url, params)
        ctx = response.context
        self.assertEqual(ctx["gross_revenue"], 0)
        self.assertEqual(ctx["net_revenue"],   0)
        self.assertEqual(ctx["cmv"],           0)
        self.assertEqual(ctx["average_ticket"], Decimal("0"))

    def test_filtro_exclui_vendas_fora_do_intervalo(self):
        """Venda de 40 dias atrás não deve aparecer ao filtrar por hoje."""
        old_sale = Sale.objects.create(
            user=self.admin,
            gross_amount=Decimal("9999.00"),
            net_amount=Decimal("9999.00"),
        )
        Sale.objects.filter(pk=old_sale.pk).update(
            status=Sale.Status.COMPLETED,
            completed_at=timezone.now() - timedelta(days=40),
        )
        self.client.force_login(self.admin)
        params = {"start_date": self.today.isoformat(), "end_date": self.today.isoformat()}
        response = self.client.get(self.url, params)
        self.assertEqual(response.context["gross_revenue"], Decimal("300.00"))
