from django.shortcuts import render
from product.services import get_filtered_products


def product_list_view(request):
    query = request.GET.get("query", "").strip()
    page_number = request.GET.get("page", 1)

    service_data = get_filtered_products(query=query, page_number=page_number)

    context = {
        "query": query,
        **service_data,  # products, paginator e page_obj
    }

    return render(request, "product/product_list.html", context)
