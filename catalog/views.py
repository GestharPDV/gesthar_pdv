import json
import urllib.parse

from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from catalog.models import CatalogConfig
from product.models import Color, Product, ProductImage, Size


def _get_config():
    return CatalogConfig.objects.first()


def _products_with_stock():
    return (
        Product.objects.filter(is_active=True)
        .annotate(
            total_stock=Coalesce(
                Sum("variations__stock", filter=Q(variations__is_active=True)),
                Value(0),
            )
        )
        .filter(total_stock__gt=0)
        .prefetch_related("variations__color", "variations__size", "images")
        .select_related("category")
    )


def _serialize_product(product):
    variations = [
        {
            "id": v.id,
            "sku": v.sku,
            "color": v.color.name,
            "size": v.size.name,
            "stock": v.stock,
        }
        for v in product.variations.filter(is_active=True, stock__gt=0)
    ]
    images = [
        {"url": img.image.url, "order": img.order}
        for img in sorted(product.images.all(), key=lambda i: i.order)
    ]
    if product.cover_image:
        cover = product.cover_image.url
    elif images:
        cover = images[0]["url"]
    else:
        cover = None

    return {
        "id": product.pk,
        "name": product.name,
        "description": product.description or "",
        "price": str(product.selling_price),
        "category": product.category.name,
        "cover": cover,
        "images": images,
        "variations": variations,
        "total_stock": product.total_stock,
    }


class CatalogListView(TemplateView):
    template_name = "catalog/catalog_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        products = _products_with_stock()

        types = list(
            Product.objects.filter(is_active=True)
            .values_list("category__name", flat=True)
            .distinct()
            .order_by("category__name")
        )
        colors = list(Color.objects.values_list("name", flat=True).order_by("name"))
        sizes = list(
            Size.objects.filter(is_active=True)
            .values_list("name", flat=True)
            .order_by("name")
        )

        ctx.update(
            {
                "products": products,
                "types": types,
                "colors": colors,
                "sizes": sizes,
                "config": _get_config(),
            }
        )
        return ctx


class ProductDetailView(View):
    def get(self, request, product_id):
        try:
            product = (
                Product.objects.filter(is_active=True)
                .annotate(
                    total_stock=Coalesce(
                        Sum(
                            "variations__stock",
                            filter=Q(variations__is_active=True),
                        ),
                        Value(0),
                    )
                )
                .prefetch_related("variations__color", "variations__size", "images")
                .select_related("category")
                .get(pk=product_id)
            )
        except Product.DoesNotExist:
            return JsonResponse({"error": "Produto não encontrado."}, status=404)

        if product.total_stock <= 0:
            return JsonResponse({"error": "Produto sem estoque."}, status=404)

        return JsonResponse(_serialize_product(product))


class SearchProductsView(View):
    def get(self, request):
        query = request.GET.get("q", "").strip()
        if not query:
            products = _products_with_stock()[:20]
            return JsonResponse(
                {"products": [_serialize_product(p) for p in products]}
            )

        products = _products_with_stock().filter(
            Q(name__icontains=query)
            | Q(category__name__icontains=query)
            | Q(variations__color__name__icontains=query)
            | Q(variations__size__name__icontains=query)
            | Q(description__icontains=query)
        ).distinct()

        return JsonResponse({"products": [_serialize_product(p) for p in products]})


class FilterProductsView(View):
    def get(self, request):
        qs = _products_with_stock()

        category = request.GET.get("type", "").strip()
        color = request.GET.get("color", "").strip()
        size = request.GET.get("size", "").strip()
        price_min = request.GET.get("price_min", "").strip()
        price_max = request.GET.get("price_max", "").strip()
        sort_by = request.GET.get("sort_by", "relevance").strip()

        if category:
            qs = qs.filter(category__name__iexact=category)
        if color:
            qs = qs.filter(variations__color__name__iexact=color, variations__is_active=True)
        if size:
            qs = qs.filter(variations__size__name__iexact=size, variations__is_active=True)
        if price_min:
            try:
                qs = qs.filter(selling_price__gte=float(price_min))
            except ValueError:
                pass
        if price_max:
            try:
                qs = qs.filter(selling_price__lte=float(price_max))
            except ValueError:
                pass

        sort_map = {
            "name_asc": "name",
            "price_asc": "selling_price",
            "price_desc": "-selling_price",
            "newest": "-created_at",
        }
        order = sort_map.get(sort_by, "name")
        qs = qs.distinct().order_by(order)

        return JsonResponse({"products": [_serialize_product(p) for p in qs]})


class WhatsAppRedirectView(View):
    def post(self, request):
        config = _get_config()
        if not config:
            return JsonResponse(
                {"error": "Configuração do catálogo não encontrada."}, status=500
            )

        try:
            data = json.loads(request.body)
            items = data.get("items", [])
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({"error": "Dados inválidos."}, status=400)

        if not items:
            return JsonResponse({"error": "Carrinho vazio."}, status=400)

        lines = ["Olá! Gostaria de fazer um pedido:\n"]
        total = 0

        for idx, item in enumerate(items, 1):
            product_id = item.get("product_id")
            variation_id = item.get("variation_id")
            quantity = int(item.get("quantity", 1))

            try:
                product = Product.objects.get(pk=product_id, is_active=True)
            except Product.DoesNotExist:
                return JsonResponse(
                    {"error": f"Produto #{product_id} não encontrado."}, status=400
                )

            variation = None
            if variation_id:
                variation = product.variations.filter(
                    pk=variation_id, is_active=True
                ).first()
                if not variation:
                    return JsonResponse(
                        {"error": f"Variação não encontrada para '{product.name}'."}, status=400
                    )
                if variation.stock < quantity:
                    return JsonResponse(
                        {
                            "error": f"Estoque insuficiente para '{product.name}' "
                            f"({variation.color.name}/{variation.size.name}). "
                            f"Disponível: {variation.stock}."
                        },
                        status=400,
                    )

            subtotal = product.selling_price * quantity
            total += subtotal

            line = f"PRODUTO {idx}\n"
            line += f"- Descrição: {product.name}\n"
            if variation:
                line += f"- Variações: Tamanho {variation.size.name}, Cor {variation.color.name}\n"
            line += f"- Quantidade: {quantity}\n"
            line += f"- Subtotal: R$ {subtotal:.2f}\n"
            lines.append(line)

        lines.append(f"TOTAL: R$ {total:.2f}")
        message = "\n".join(lines)

        whatsapp_url = (
            f"https://wa.me/{config.whatsapp_number}"
            f"?text={urllib.parse.quote(message)}"
        )
        return JsonResponse({"url": whatsapp_url})
