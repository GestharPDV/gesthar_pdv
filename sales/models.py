# sales/models.py
# Arquivo completo e profissional para o app de Vendas

import math
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import F, Sum, Value, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.exceptions import ValidationError

# --- Dependências de outros Apps ---
# Model de Produto (para saber O QUE foi vendido)
from product.models import ProductVariation 

# Model de Usuário (para saber QUEM vendeu e QUEM operou o caixa)
from user.models import UserGesthar 

# Model de Cliente (para saber PARA QUEM foi vendido)
from customer.models import Customer 


# -----------------------------------------------------------------------------
# Model de Caixa (Baseado no ERD: CAIXA)
# -----------------------------------------------------------------------------
class CashRegister(models.Model):
    """
    Gerencia a abertura, fechamento e movimentações de um caixa.
    Representa uma "sessão" de trabalho de um usuário.
    """
    class CashRegisterStatus(models.TextChoices):
        OPEN = "OPEN", "Aberto"
        CLOSED = "CLOSED", "Fechado"

    user = models.ForeignKey(
        UserGesthar,
        on_delete=models.PROTECT,
        related_name="cash_registers",
        verbose_name="Usuário"
    )
    status = models.CharField(
        max_length=10, 
        choices=CashRegisterStatus.choices, 
        default=CashRegisterStatus.OPEN,
        verbose_name="Status"
    )
    
    # Datas
    opening_time = models.DateTimeField(
        default=timezone.now, verbose_name="Data de Abertura"
    )
    closing_time = models.DateTimeField(
        blank=True, null=True, verbose_name="Data de Fechamento"
    )

    # Valores Iniciais
    initial_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor Inicial (Troco)",
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    # Valores de Fechamento (O que o usuário INFORMA ter contado)
    final_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor Final (Informado)"
    )
    
    # Valores Calculados (O que o SISTEMA calcula)
    total_sales = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total em Vendas (Calculado)"
    )
    total_withdrawals = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total de Sangrias"
    )
    total_deposits = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total de Suprimentos"
    )
    difference = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Diferença (Quebra de Caixa)"
    )

    class Meta:
        verbose_name = "Caixa"
        verbose_name_plural = "Caixas"
        ordering = ["-opening_time"]
        constraints = [
            # Regra de Negócio: Um usuário só pode ter um caixa aberto por vez.
            models.UniqueConstraint(
                fields=["user"],
                # CORREÇÃO APLICADA AQUI:
                condition=Q(status="OPEN"),
                name="unique_open_cash_register_per_user"
            )
        ]

    def __str__(self):
        # Formata a data para um padrão mais legível (ex: 25/10/2025 14:30)
        return f"Caixa de {self.user.get_full_name()} ({self.opening_time.strftime('%d/%m/%Y %H:%M')}) - {self.get_status_display()}"

    def clean(self):
        super().clean()
        # Regra de negócio: Se está fechando, o valor final é obrigatório.
        # Note que aqui "self.CashRegisterStatus.CLOSED" funciona, pois
        # dentro de um método, 'self' nos dá o escopo correto.
        if self.status == self.CashRegisterStatus.CLOSED and self.final_value is None:
             raise ValidationError("O 'Valor Final Informado' é obrigatório para fechar o caixa.")
        
        # Garante que o horário de fechamento seja registrado
        if self.status == self.CashRegisterStatus.CLOSED and not self.closing_time:
             self.closing_time = timezone.now()


# -----------------------------------------------------------------------------
# Model de Venda (Baseado no ERD: VENDA)
# -----------------------------------------------------------------------------
class Sale(models.Model):
    """
    Registra o "cabeçalho" da Venda.
    Associa Cliente, Vendedor, Caixa e os valores totais.
    """
    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Dinheiro"
        CREDIT_CARD = "CREDIT_CARD", "Cartão de Crédito"
        DEBIT_CARD = "DEBIT_CARD", "Cartão de Débito"
        PIX = "PIX", "Pix"
        BANK_SLIP = "BANK_SLIP", "Boleto"
        OTHER = "OTHER", "Outro"

    class SaleStatus(models.TextChoices):
        PENDING = "PENDING", "Pendente" # Pode ser um orçamento
        COMPLETED = "COMPLETED", "Concluída" # Paga e finalizada
        CANCELLED = "CANCELLED", "Cancelada" # Venda desfeita

    # --- Relacionamentos Fundamentais ---
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT, # Protege o histórico de vendas do cliente
        related_name="sales",
        verbose_name="Cliente"
    )
    user = models.ForeignKey(
        UserGesthar,
        on_delete=models.PROTECT, # Protege o histórico do vendedor
        related_name="sales",
        verbose_name="Vendedor"
    )
    cash_register = models.ForeignKey(
        CashRegister,
        on_delete=models.PROTECT, # Protege o histórico do caixa
        related_name="sales",
        verbose_name="Caixa"
    )

    # --- Data e Status ---
    sale_date = models.DateTimeField(default=timezone.now, verbose_name="Data da Venda")
    status = models.CharField(
        max_length=20,
        choices=SaleStatus.choices,
        default=SaleStatus.PENDING,
        verbose_name="Status"
    )

    # --- Valores Totais ---
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Subtotal"
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Desconto (R$)",
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Total"
    )

    # --- Pagamento ---
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        verbose_name="Forma de Pagamento"
    )
    installments = models.PositiveIntegerField(
        default=1,
        verbose_name="Parcelas",
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ["-sale_date"]

    def __str__(self):
        return f"Venda #{self.id} - {self.customer.name} - {self.get_status_display()}"

    def update_totals(self):
        """
        Calcula o subtotal e o total da venda com base nos seus itens.
        É chamado pelo 'save()' do SaleItem.
        """
        # Coalesce(Sum('...'), 0) é uma forma segura de somar, garantindo que
        # se não houver itens (None), o resultado seja 0 em vez de erro.
        sale_subtotal = self.items.aggregate(
            total_sub=Coalesce(Sum('subtotal'), Decimal('0.00'))
        )['total_sub']

        self.subtotal = sale_subtotal
        
        # Garante que o desconto não seja maior que o subtotal
        if self.discount > self.subtotal:
            self.discount = self.subtotal
            
        self.total = self.subtotal - self.discount
        
        # O total nunca pode ser negativo
        if self.total < 0:
            self.total = Decimal("0.00")

    def save(self, *args, **kwargs):
        # Atualiza os totais sempre que a Venda for salva
        # (especialmente quando um SaleItem é salvo e chama este método)
        self.update_totals() 
        super().save(*args, **kwargs)


# -----------------------------------------------------------------------------
# Model de Item da Venda (Baseado no ERD: ITEM_VENDA)
# -----------------------------------------------------------------------------
class SaleItem(models.Model):
    """
    Registra cada item (produto) dentro de uma Venda.
    Esta é a "linha" da nota fiscal.
    """
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE, # Se a Venda for apagada, os itens vão junto
        related_name="items", # Permite fazer sale.items.all()
        verbose_name="Venda"
    )
    
    product_variation = models.ForeignKey(
        ProductVariation,
        on_delete=models.PROTECT, # Protege o histórico de vendas do produto
        related_name="sale_items",
        verbose_name="Variação do Produto"
    )

    quantity = models.PositiveIntegerField(
        verbose_name="Quantidade",
        validators=[MinValueValidator(1)]
    )

    # --- Preços no Momento da Venda (Histórico) ---
    # Armazena o preço do produto NO MOMENTO DA VENDA, para garantir
    # que o histórico financeiro não mude se o preço do produto for alterado.
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Preço Unitário (na Venda)"
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Desconto (R$)",
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Subtotal do Item"
    )

    class Meta:
        verbose_name = "Item da Venda"
        verbose_name_plural = "Itens da Venda"
        constraints = [
            # Regra de Negócio: Impede que o MESMO produto seja adicionado
            # DUAS VEZES na MESMA venda.
            models.UniqueConstraint(
                fields=["sale", "product_variation"],
                name="unique_sale_product_variation"
            )
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product_variation.sku} (Venda #{self.sale.id})"

    def clean(self):
        super().clean()
        # Garante que o desconto do item não seja maior que o preço total do item
        total_price = self.unit_price * self.quantity
        if self.discount > total_price:
            raise ValidationError(
                f"O desconto do item (R$ {self.discount}) não pode ser maior que "
                f"o valor total dos itens (R$ {total_price})."
            )

    def save(self, *args, **kwargs):
        # 1. Calcula o SEU PRÓPRIO subtotal
        self.subtotal = (self.unit_price * self.quantity) - self.discount
        if self.subtotal < 0:
            self.subtotal = Decimal("0.00")
            
        super().save(*args, **kwargs) # Salva o item
        
        # 2. "AVISA" a Venda-pai que ela precisa se recalcular
        # Isso aciona o Sale.save() que chama o Sale.update_totals()
        self.sale.save()