# product/services/product_services.py
from django.db.models import Q
from django.core.paginator import Paginator
from product.models import Category, Color, Product, Size, Supplier
from .utils import standardize_name


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


class ServiceValidationError(ValueError):
    """Erro de validação de dados (Ex: nome em branco)."""

    pass


class ServiceDuplicateError(ValueError):
    """Erro de violação de unicidade (Ex: nome já existe)."""

    pass


def create_category(name: str) -> Category:
    """
    Cria uma nova Categoria.

    Args:
        name: O nome da categoria.

    Returns:
        O objeto Category criado.

    Raises:
        ServiceValidationError: Se o nome for nulo ou vazio.
        ServiceDuplicateError: Se a categoria já existir.
    """
    if not name or not name.strip():
        raise ServiceValidationError("O nome é obrigatório.")

    # Seu StandardizeNameMixin deve ser executado pelo .save() do get_or_create
    category, created = Category.objects.get_or_create(name=standardize_name(name))

    if not created:
        raise ServiceDuplicateError("Uma categoria com este nome já existe.")

    return category


def create_supplier(name: str) -> Supplier:
    if not name or not name.strip():
        raise ServiceValidationError("O nome é obrigatório.")

    supplier, created = Supplier.objects.get_or_create(name=standardize_name(name))

    if not created:
        raise ServiceDuplicateError("Um fornecedor com este nome já existe.")

    return supplier


def create_color(name: str) -> Color:
    if not name or not name.strip():
        raise ServiceValidationError("O nome é obrigatório.")

    color, created = Color.objects.get_or_create(name=standardize_name(name))

    if not created:
        raise ServiceDuplicateError("Uma cor com este nome já existe.")

    return color


def create_size(name: str) -> Size:
    if not name or not name.strip():
        raise ServiceValidationError("O nome é obrigatório.")

    size, created = Size.objects.get_or_create(name=standardize_name(name))

    if not created:
        raise ServiceDuplicateError("Um tamanho com este nome já existe.")

    return size
