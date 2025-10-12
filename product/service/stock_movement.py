from django.db import transaction
from decimal import Decimal
from user.models import UserGesthar
from product.models import StockMovement, ProductVariation


@transaction.atomic
def add_stock(
    product_variation_id: int,
    quantity: int,
    user: UserGesthar,
    unit_price: Decimal,
    movement_type: str = StockMovement.MovementType.ENTRADA,
    notes: str = None,
):
    """
    Adiciona uma quantidade de estoque a uma variação de produto e registra o movimento de forma atômica.
    """
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
        movement_type=movement_type,
        notes=notes,
    )

    return product_variation
