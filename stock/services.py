import json
from datetime import date
from django.db import transaction
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Value
from django.db.models.functions import Coalesce
from decimal import Decimal
from user.models import UserGesthar
from product.models import ProductVariation, Category
from .models import StockMovement


# ---------------------------------------------------------------------------
# Funções de Relatório de Estoque (RF016)
# ---------------------------------------------------------------------------

def get_total_pieces() -> int:
    """
    Retorna o total físico de peças em estoque,
    somando o campo `stock` de todas as variações ativas.
    """
    result = (
        ProductVariation.active
        .aggregate(total=Coalesce(Sum("stock"), Value(0)))
    )
    return result["total"]


def get_inventory_valuation() -> Decimal:
    """
    Retorna o valor total do estoque (quantidade × preço de venda do produto pai)
    para todas as variações ativas.
    """
    result = (
        ProductVariation.active
        .annotate(
            line_value=ExpressionWrapper(
                F("stock") * F("product__selling_price"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
        .aggregate(total=Coalesce(Sum("line_value"), Value(Decimal("0.00"))))
    )
    return result["total"]


def get_low_stock_variations():
    """
    Retorna as variações ativas cujo estoque atual é menor ou igual
    ao `minimum_stock` definido para aquela variação.
    Inclui dados do produto, cor e tamanho via select_related para evitar N+1.
    """
    return (
        ProductVariation.active
        .filter(stock__lte=F("minimum_stock"))
        .select_related("product", "color", "size", "product__category")
        .order_by("product__name", "color__name", "size__name")
    )


def get_inventory_movements(start_date: date, end_date: date):
    """
    Retorna os movimentos de estoque registrados no período [start_date, end_date].
    O filtro usa `movement_date__date` para comparar apenas a parte da data.
    """
    return (
        StockMovement.objects
        .filter(movement_date__date__gte=start_date, movement_date__date__lte=end_date)
        .select_related(
            "product_variation__product",
            "product_variation__color",
            "product_variation__size",
            "user",
        )
        .order_by("-movement_date")
    )


def get_quantity_by_category() -> dict:
    """
    Agrupa o estoque total por categoria (apenas variações ativas).
    Retorna um dict {nome_categoria: total_estoque} para uso no gráfico de pizza.
    """
    rows = (
        ProductVariation.active
        .values(category_name=F("product__category__name"))
        .annotate(total=Coalesce(Sum("stock"), Value(0)))
        .order_by("category_name")
    )
    return {row["category_name"]: row["total"] for row in rows}


def get_quantity_by_color() -> dict:
    """
    Agrupa o estoque total por cor (apenas variações ativas).
    Retorna um dict {nome_cor: total_estoque} para uso no gráfico de barras.
    """
    rows = (
        ProductVariation.active
        .values(color_name=F("color__name"))
        .annotate(total=Coalesce(Sum("stock"), Value(0)))
        .order_by("color_name")
    )
    return {row["color_name"]: row["total"] for row in rows}


def get_all_categories():
    """Retorna todas as categorias ativas para popular o filtro do relatório."""
    return Category.objects.filter(is_active=True).order_by("name")

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