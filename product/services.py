# product/services/product_services.py
from django.db.models import Q
from django.core.paginator import Paginator
from product.models import Product


def get_filtered_products(query: str = "", page_number: int = 1, per_page: int = 10):
    """
    Serviço que retorna produtos com filtros, paginação e anotações de estoque e margem de lucro.
    """
    products = (
        Product.objects.with_stock()
        .with_average_profit_margin()
        .select_related("category")
        .prefetch_related("suppliers")
        .order_by("name")
    )

    # Filtro de busca (nome, categoria ou SKU)
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(category__name__icontains=query)
            | Q(variations__sku__icontains=query)
        ).distinct()

    # Paginação
    paginator = Paginator(products, per_page)
    page_obj = paginator.get_page(page_number)

    return {
        "products": page_obj,  # objeto paginado pronto para o template
        "paginator": paginator,
        "page_obj": page_obj,
    }
