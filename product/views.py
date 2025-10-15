from django.shortcuts import render
from .models import ProductVariation

def visualizar_produtos(request):
    variations = ProductVariation.objects.select_related(
        'product__category', 
        'color', 
        'size'
    ).all()
    return render(request, 'product/visualizar_produtos.html', {'variations': variations})
