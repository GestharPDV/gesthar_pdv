# sales/services.py
from django.db import transaction
from decimal import Decimal

# Importe os serviços que você JÁ TEM
from stock.services import remove_stock
from stock.models import StockMovement

# Importe os models do app 'sales'
from .models import Sale, SaleItem, CashRegister

class SaleCompletionError(Exception):
    """Exceção customizada para erros ao finalizar a venda."""
    pass

@transaction.atomic
def complete_sale(sale: Sale):
    """
    Finaliza uma Venda:
    1. Trava a venda e os itens para a transação.
    2. Itera sobre cada SaleItem e dá baixa no estoque.
    3. Atualiza o status da Venda para "COMPLETED".
    4. Atualiza o 'total_sales' do Caixa associado.
    """
    
    # 1. Garante que a venda esteja em um estado válido para finalização
    if sale.status == Sale.SaleStatus.COMPLETED:
        raise SaleCompletionError("Esta venda já foi concluída.")
        
    if sale.status == Sale.SaleStatus.CANCELLED:
        raise SaleCompletionError("Não é possível concluir uma venda cancelada.")

    # 2. Trava a venda no banco de dados para evitar condições de corrida
    #    (Ex: dois usuários tentando finalizar a mesma venda ao mesmo tempo)
    try:
        sale_to_complete = Sale.objects.select_for_update().get(pk=sale.pk)
    except Sale.DoesNotExist:
        raise SaleCompletionError("Venda não encontrada.")

    # 3. Itera sobre os itens e dá baixa no estoque
    items = sale_to_complete.items.select_related('product_variation').all()
    
    if not items:
        raise SaleCompletionError("Não é possível concluir uma venda sem itens.")

    for item in items:
        try:
            remove_stock(
                product_variation_id=item.product_variation.id,
                quantity=item.quantity,
                user=sale_to_complete.user, # O vendedor que realizou a venda
                movement_type=StockMovement.MovementType.SAIDA,
                notes=f"Saída referente à Venda #{sale_to_complete.id}"
            )
        except ValueError as e:
            # Pega o erro de "Estoque insuficiente" do seu serviço de stock
            raise SaleCompletionError(
                f"Erro ao dar baixa no item {item.product_variation.sku}: {str(e)}"
            )

    # 4. Atualiza o status da Venda
    sale_to_complete.status = Sale.SaleStatus.COMPLETED
    sale_to_complete.save()

    # 5. Atualiza o total de vendas no Caixa
    cash_register = sale_to_complete.cash_register
    if cash_register.status == CashRegister.CashRegisterStatus.OPEN:
        cash_register.total_sales += sale_to_complete.total
        cash_register.save()
    
    return sale_to_complete