import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import View
from django.db import transaction
from django.views.decorators.http import require_POST
from product.services import ServiceDuplicateError, ServiceValidationError, create_category, create_supplier, get_filtered_products
from .forms import ProductForm, ProductSupplierFormSet, ProductVariationFormSet
from .models import Category, Supplier


class ProductCreateView(View):
    template_name = 'product/product_form.html'

    def get(self, request, *args, **kwargs):
        product_form = ProductForm()

        supplier_formset = ProductSupplierFormSet(prefix='suppliers')
        variation_formset = ProductVariationFormSet(prefix='variations')

        context = {
            'product_form': product_form,
            'supplier_formset': supplier_formset,
            'variation_formset': variation_formset,
        }
        return render(request, self.template_name, context)
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        product_form = ProductForm(request.POST)
        supplier_formset = ProductSupplierFormSet(request.POST, prefix='suppliers')
        variation_formset = ProductVariationFormSet(request.POST, prefix='variations')

        # Valida todos os formulários
        is_product_form_valid = product_form.is_valid()
        is_supplier_formset_valid = supplier_formset.is_valid()
        is_variation_formset_valid = variation_formset.is_valid()

        # O campo 'has_variation' determina se o formset de variações deve ser validado
        has_variation = product_form.cleaned_data.get('has_variation', False)
        
        # A validação das variações só é obrigatória se o checkbox 'has_variation' estiver marcado
        variation_check_passed = (not has_variation) or is_variation_formset_valid

        if is_product_form_valid and is_supplier_formset_valid and variation_check_passed:
            # Primeiro, salva o produto para obter um ID
            product = product_form.save()

            # Associa os formsets ao produto recém-criado
            supplier_formset.instance = product
            supplier_formset.save()
            
            # Salva variações apenas se o produto foi marcado para tê-las
            if has_variation:
                variation_formset.instance = product
                variation_formset.save()

            messages.success(request, f'Produto "{product.name}" cadastrado com sucesso!')
            return redirect(reverse_lazy('product:product-list')) 
        
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
            context = {
                'product_form': product_form,
                'supplier_formset': supplier_formset,
                'variation_formset': variation_formset,
            }
            return render(request, self.template_name, context)

def product_list_view(request):
    query = request.GET.get("query", "").strip()
    page_number = request.GET.get("page", 1)

    service_data = get_filtered_products(query=query, page_number=page_number)

    context = {
        "query": query,
        **service_data,  # products, paginator e page_obj
    }

    return render(request, "product/product_list.html", context)

@require_POST
def category_create_view(request):
    """
    View AJAX para criar uma nova Categoria.
    Lida com o request/response HTTP e chama o serviço.
    """
    try:
        # 1. Responsabilidade da View: Lidar com HTTP
        data = json.loads(request.body)
        name = data.get('name')

        # 2. Responsabilidade da View: Chamar o Serviço
        category = create_category(name=name)

        # 3. Responsabilidade da View: Formatar Resposta de Sucesso
        return JsonResponse({
            'status': 'success',
            'id': category.id,
            'name': category.name
        }, status=201)

    # 4. Responsabilidade da View: Tratar exceções e traduzir para HTTP
    except (ServiceValidationError, ServiceDuplicateError) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Corpo da requisição JSON inválido.'}, status=400)

    except Exception as e:
        # Idealmente, você logaria esse erro (logger.error(e))
        return JsonResponse({'status': 'error', 'message': 'Ocorreu um erro inesperado.'}, status=500)
    

@require_POST
def supplier_create_view(request):
    """
    View AJAX para criar um novo Fornecedor.
    Lida com o request/response HTTP e chama o serviço.
    """
    try:
        # 1. Lidar com HTTP
        data = json.loads(request.body)
        name = data.get('name')

        # 2. Chamar o Serviço
        supplier = create_supplier(name=name)

        # 3. Formatar Resposta de Sucesso
        return JsonResponse({
            'status': 'success',
            'id': supplier.id,
            'name': supplier.name
        }, status=201)

    # 4. Tratar exceções
    except (ServiceValidationError, ServiceDuplicateError) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Corpo da requisição JSON inválido.'}, status=400)
        
    except Exception as e:
        # logger.error(e)
        return JsonResponse({'status': 'error', 'message': 'Ocorreu um erro inesperado.'}, status=500)