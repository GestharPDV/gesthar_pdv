import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import View
from django.db import transaction
from django.views.decorators.http import require_POST
from product.services import (
    ServiceDuplicateError,
    ServiceValidationError,
    create_category,
    create_supplier,
    create_color,
    create_size,
    get_filtered_products,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import Product
from .forms import ProductForm, ProductSupplierFormSet, ProductVariationFormSet


class ProductCreateView(LoginRequiredMixin, View):
    template_name = "product/product_form.html"

    def get(self, request, *args, **kwargs):
        product_form = ProductForm()

        supplier_formset = ProductSupplierFormSet(prefix="suppliers")
        variation_formset = ProductVariationFormSet(prefix="variations")

        context = {
            "product_form": product_form,
            "supplier_formset": supplier_formset,
            "variation_formset": variation_formset,
            "page_title": "Cadastro de Produto",
            "button_text": "Finalizar Cadastro",
        }
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        product_form = ProductForm(request.POST)
        supplier_formset = ProductSupplierFormSet(request.POST, prefix="suppliers")
        variation_formset = ProductVariationFormSet(request.POST, prefix="variations")

        # Valida todos os formulários
        is_product_form_valid = product_form.is_valid()
        is_supplier_formset_valid = supplier_formset.is_valid()
        is_variation_formset_valid = variation_formset.is_valid()

        if (
            is_product_form_valid
            and is_supplier_formset_valid
            and is_variation_formset_valid
        ):
            # Primeiro, salva o produto para obter um ID
            product = product_form.save()

            # Associa os formsets ao produto recém-criado
            supplier_formset.instance = product
            supplier_formset.save()

            variation_formset.instance = product
            variation_formset.save()

            messages.success(
                request, f'Produto "{product.name}" cadastrado com sucesso!'
            )
            return redirect(reverse_lazy("product:product-list"))

        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
            context = {
                "product_form": product_form,
                "supplier_formset": supplier_formset,
                "variation_formset": variation_formset,
                "page_title": "Cadastro de Produto",
                "button_text": "Finalizar Cadastro",
            }
            return render(request, self.template_name, context)


class ProductUpdateView(LoginRequiredMixin, View):
    template_name = "product/product_form.html"

    def get(self, request, pk, *args, **kwargs):
        # 1. Busca o produto existente ou retorna 404
        product = get_object_or_404(Product, pk=pk)

        # 2. Pré-preenche os formulários com a 'instance' do produto
        product_form = ProductForm(instance=product)
        supplier_formset = ProductSupplierFormSet(instance=product, prefix="suppliers")
        variation_formset = ProductVariationFormSet(
            instance=product, prefix="variations"
        )

        context = {
            "product_form": product_form,
            "supplier_formset": supplier_formset,
            "variation_formset": variation_formset,
            "page_title": "Editar Produto",  # [MUDOU]
            "button_text": "Salvar Alterações",  # [MUDOU]
        }
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk)

        product_form = ProductForm(request.POST, instance=product)
        supplier_formset = ProductSupplierFormSet(
            request.POST, instance=product, prefix="suppliers"
        )
        variation_formset = ProductVariationFormSet(
            request.POST, instance=product, prefix="variations"
        )

        is_product_form_valid = product_form.is_valid()
        is_supplier_formset_valid = supplier_formset.is_valid()
        is_variation_formset_valid = variation_formset.is_valid()

        if (
            is_product_form_valid
            and is_supplier_formset_valid
            and is_variation_formset_valid
        ):

            product = product_form.save()
            supplier_formset.save()
            variation_formset.save()

            messages.success(
                request, f'Produto "{product.name}" atualizado com sucesso!'
            )
            return redirect(reverse_lazy("product:product-list"))
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
            context = {
                "product_form": product_form,
                "supplier_formset": supplier_formset,
                "variation_formset": variation_formset,
                "page_title": "Editar Produto",
                "button_text": "Salvar Alterações",
            }
            return render(request, self.template_name, context)


@login_required
def product_list_view(request):
    query = request.GET.get("query", "").strip()
    page_number = request.GET.get("page", 1)

    service_data = get_filtered_products(query=query, page_number=page_number)

    context = {
        "query": query,
        **service_data,  # products, paginator e page_obj
    }

    return render(request, "product/product_list.html", context)


@login_required
def product_detail_view(request, pk):
    product = get_object_or_404(Product.objects.with_average_profit_margin(), pk=pk)

    variations = product.variations.select_related("color", "size").order_by(
        "color", "size"
    )
    suppliers = product.productsupplier_set.select_related("supplier").order_by(
        "supplier__name"
    )
    # Escolhe um fornecedor primário (o primeiro ordenado por nome) para exibir nas variações
    primary_supplier = suppliers.first() if suppliers.exists() else None
    profit_value = product.selling_price - product.average_cost_price

    context = {
        "product": product,
        "variations": variations,
        "suppliers": suppliers,
        "primary_supplier": primary_supplier,
        "profit_value": profit_value,
        "page_title": f"Detalhes: {product.name}",
    }

    return render(request, "product/product_detail.html", context)


@login_required
@require_POST
def category_create_view(request):
    """
    View AJAX para criar uma nova Categoria.
    Lida com o request/response HTTP e chama o serviço.
    """
    try:
        # 1. Responsabilidade da View: Lidar com HTTP
        data = json.loads(request.body)
        name = data.get("name")

        # 2. Responsabilidade da View: Chamar o Serviço
        category = create_category(name=name)

        # 3. Responsabilidade da View: Formatar Resposta de Sucesso
        return JsonResponse(
            {"status": "success", "id": category.id, "name": category.name}, status=201
        )

    # 4. Responsabilidade da View: Tratar exceções e traduzir para HTTP
    except (ServiceValidationError, ServiceDuplicateError) as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Corpo da requisição JSON inválido."},
            status=400,
        )

    except Exception as e:
        # Idealmente, você logaria esse erro (logger.error(e))
        return JsonResponse(
            {"status": "error", "message": "Ocorreu um erro inesperado."}, status=500
        )


@login_required
@require_POST
def supplier_create_view(request):
    """
    View AJAX para criar um novo Fornecedor.
    Lida com o request/response HTTP e chama o serviço.
    """
    try:
        # 1. Lidar com HTTP
        data = json.loads(request.body)
        name = data.get("name")

        # 2. Chamar o Serviço
        supplier = create_supplier(name=name)

        # 3. Formatar Resposta de Sucesso
        return JsonResponse(
            {"status": "success", "id": supplier.id, "name": supplier.name}, status=201
        )

    # 4. Tratar exceções
    except (ServiceValidationError, ServiceDuplicateError) as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Corpo da requisição JSON inválido."},
            status=400,
        )

    except Exception as e:
        # logger.error(e)
        return JsonResponse(
            {"status": "error", "message": "Ocorreu um erro inesperado."}, status=500
        )


@login_required
@require_POST
def color_create_view(request):
    try:
        data = json.loads(request.body)
        name = data.get("name")

        color = create_color(name=name)

        return JsonResponse(
            {"status": "success", "id": color.id, "name": color.name}, status=201
        )

    except (ServiceValidationError, ServiceDuplicateError) as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Corpo da requisição JSON inválido."},
            status=400,
        )

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": "Ocorreu um erro inesperado."}, status=500
        )


@login_required
@require_POST
def size_create_view(request):
    try:
        data = json.loads(request.body)
        name = data.get("name")

        size = create_size(name=name)

        return JsonResponse(
            {"status": "success", "id": size.id, "name": size.name}, status=201
        )

    except (ServiceValidationError, ServiceDuplicateError) as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Corpo da requisição JSON inválido."},
            status=400,
        )

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": "Ocorreu um erro inesperado."}, status=500
        )


@login_required
@require_POST
def product_delete_view(request, pk):
    """
    View para excluir (desativar) um produto.
    """
    product = get_object_or_404(Product, pk=pk)
    product_name = product.name
    
    # Desativa o produto ao invés de excluir permanentemente
    product.is_active = False
    product.save()
    
    messages.success(request, f'Produto "{product_name}" excluído com sucesso!')
    return redirect("product:product-list")