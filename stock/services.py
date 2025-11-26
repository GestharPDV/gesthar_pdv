from django.db import transaction
from decimal import Decimal
from user.models import UserGesthar
from product.models import ProductVariation
from .models import StockMovement

@transaction.atomic
def add_stock(
    product_variation_id: int,
    quantity: int,
    user: UserGesthar,
    unit_price: Decimal,
    supplier_id: int = None,
    movement_type: str = StockMovement.MovementType.ENTRADA,
    notes: str = None,
):
    """
    Adiciona uma quantidade de estoque a uma variação de produto e registra o movimento de forma atômica.
    """
    VALID_MOVEMENT_TYPES = {
        StockMovement.MovementType.ENTRADA,
        StockMovement.MovementType.AJUSTE_ENTRADA,
        StockMovement.MovementType.DEVOLUCAO,
    }
    if movement_type not in VALID_MOVEMENT_TYPES:
        raise ValueError(f"Tipo de movimento inválido para adição de estoque: {movement_type}")

    try:
        product_variation = ProductVariation.objects.select_for_update().get(
            id=product_variation_id
        )
    except ProductVariation.DoesNotExist:
        raise ValueError("Variação de produto não encontrada.")

    # Atualiza o estoque da variação do produto
    product_variation.stock += quantity
    product_variation.save()

    # Registra o movimento de estoque
    StockMovement.objects.create(
        product_variation=product_variation,
        quantity=quantity,
        user=user,
        unit_price=unit_price,
        supplier_id=supplier_id,
        movement_type=movement_type,
        notes=notes,
    )

    return product_variation


@transaction.atomic
def remove_stock(
    product_variation_id: int,
    quantity: int,
    user: UserGesthar,
    movement_type: str = StockMovement.MovementType.SAIDA,
    notes: str = None,
):
    """
    Remove uma quantidade de estoque de uma variação de produto e registra o movimento de forma atômica. Garante que o estoque não fique negativo.
    """
    VALID_MOVEMENT_TYPES = {
        StockMovement.MovementType.VENDA,
        StockMovement.MovementType.SAIDA,
        StockMovement.MovementType.AJUSTE_SAIDA,
    }

    if movement_type not in VALID_MOVEMENT_TYPES:
        raise ValueError(f"Tipo de movimento inválido para remoção de estoque: {movement_type}")

    if quantity <= 0:
        raise ValueError("A quantidade a ser removida deve ser maior que zero.")
    
    try:
        product_variation = ProductVariation.objects.select_for_update().get(
            id=product_variation_id
        )
    except ProductVariation.DoesNotExist:
        raise ValueError("Variação de produto não encontrada.")

    if product_variation.stock < quantity:
        raise ValueError(
            f"Estoque insuficiente para a remoção solicitada. Estoque atual: {product_variation.stock}, Quantidade solicitada: {quantity}"
        )

    product_variation.stock -= quantity
    product_variation.save()

    StockMovement.objects.create(
        product_variation=product_variation,
        quantity=quantity,
        user=user,
        movement_type=movement_type,
        notes=notes,
    )

    return product_variation