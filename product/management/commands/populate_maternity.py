# product/management/commands/populate_maternity.py
from django.core.management.base import BaseCommand
from django.db import transaction
from product.models import Product, Category, Color, Size, Supplier, ProductVariation, ProductSupplier
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Povoa o banco de dados com 20 produtos de teste para Moda Gestante'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando povoamento massivo...')

        try:
            with transaction.atomic():
                # 1. Criar Categorias
                cat_gestante, _ = Category.objects.get_or_create(
                    name='Moda Gestante', 
                    defaults={'description': 'Roupas casuais e sociais para gestantes'}
                )
                cat_lingerie, _ = Category.objects.get_or_create(
                    name='Lingerie Maternidade',
                    defaults={'description': 'Sutiãs, calcinhas e cintas'}
                )
                cat_pijama, _ = Category.objects.get_or_create(
                    name='Pijamas e Camisolas',
                    defaults={'description': 'Linha noite para gestante e amamentação'}
                )
                self.stdout.write(self.style.SUCCESS('Categorias verificadas.'))

                # 2. Criar Tamanhos
                sizes = ['P', 'M', 'G', 'GG', 'XG', '38', '40', '42', '44', '46']
                size_objs = {}
                for s in sizes:
                    obj, _ = Size.objects.get_or_create(name=s)
                    size_objs[s] = obj

                # 3. Criar Cores
                colors = [
                    'Preto', 'Branco', 'Bege', 'Rosa Bebê', 'Azul Marinho', 
                    'Cinza Mescla', 'Vinho', 'Verde Militar', 'Estampado Floral', 'Listrado'
                ]
                color_objs = {}
                for c in colors:
                    obj, _ = Color.objects.get_or_create(name=c)
                    color_objs[c] = obj

                # 4. Criar Fornecedor
                supplier, _ = Supplier.objects.get_or_create(name='Fornecedor Gestante SP')

                # 5. Lista de 20 Produtos
                products_data = [
                    # --- ROUPAS GESTANTE ---
                    {'name': 'Vestido Midi Canelado', 'price': '89.90', 'cost': '45.00', 'cat': cat_gestante, 'cols': ['Preto', 'Vinho', 'Cinza Mescla'], 'sz': ['P', 'M', 'G', 'GG']},
                    {'name': 'Calça Jeans Cós Elástico', 'price': '129.90', 'cost': '60.00', 'cat': cat_gestante, 'cols': ['Azul Marinho'], 'sz': ['38', '40', '42', '44', '46']},
                    {'name': 'Bata Soltinha Viscose', 'price': '79.90', 'cost': '35.00', 'cat': cat_gestante, 'cols': ['Branco', 'Estampado Floral'], 'sz': ['P', 'M', 'G']},
                    {'name': 'Shorts Gestante Linho', 'price': '89.90', 'cost': '40.00', 'cat': cat_gestante, 'cols': ['Bege', 'Preto', 'Verde Militar'], 'sz': ['P', 'M', 'G', 'GG']},
                    {'name': 'Legging Gestante Básica', 'price': '59.90', 'cost': '25.00', 'cat': cat_gestante, 'cols': ['Preto', 'Cinza Mescla', 'Azul Marinho'], 'sz': ['P', 'M', 'G', 'GG', 'XG']},
                    {'name': 'Macacão Longo Malha', 'price': '119.90', 'cost': '55.00', 'cat': cat_gestante, 'cols': ['Preto', 'Verde Militar'], 'sz': ['M', 'G', 'GG']},
                    {'name': 'Blusa Amamentação Transpassada', 'price': '69.90', 'cost': '30.00', 'cat': cat_gestante, 'cols': ['Rosa Bebê', 'Branco', 'Listrado'], 'sz': ['P', 'M', 'G', 'GG']},
                    {'name': 'Vestido Longo Estampado', 'price': '149.90', 'cost': '70.00', 'cat': cat_gestante, 'cols': ['Estampado Floral'], 'sz': ['P', 'M', 'G']},
                    {'name': 'Saia Midi Malha', 'price': '79.90', 'cost': '35.00', 'cat': cat_gestante, 'cols': ['Preto', 'Listrado'], 'sz': ['P', 'M', 'G']},
                    {'name': 'Regata Básica Gestante', 'price': '39.90', 'cost': '15.00', 'cat': cat_gestante, 'cols': ['Branco', 'Preto', 'Cinza Mescla'], 'sz': ['P', 'M', 'G', 'GG']},
                    {'name': 'Cardigan Alongado Tricô', 'price': '99.90', 'cost': '45.00', 'cat': cat_gestante, 'cols': ['Bege', 'Cinza Mescla', 'Preto'], 'sz': ['P', 'M', 'G']},
                    {'name': 'Vestido Festa Gestante Renda', 'price': '199.90', 'cost': '90.00', 'cat': cat_gestante, 'cols': ['Azul Marinho', 'Vinho'], 'sz': ['P', 'M', 'G', 'GG']},
                    {'name': 'Jardineira Jeans Gestante', 'price': '159.90', 'cost': '75.00', 'cat': cat_gestante, 'cols': ['Azul Marinho'], 'sz': ['38', '40', '42', '44']},
                    
                    # --- LINGERIE ---
                    {'name': 'Sutiã Amamentação Renda', 'price': '59.90', 'cost': '25.00', 'cat': cat_lingerie, 'cols': ['Branco', 'Bege', 'Preto', 'Rosa Bebê'], 'sz': ['M', 'G', 'GG']},
                    {'name': 'Cinta Pós-Parto Modeladora', 'price': '89.90', 'cost': '40.00', 'cat': cat_lingerie, 'cols': ['Bege'], 'sz': ['P', 'M', 'G', 'GG']},
                    {'name': 'Calcinha Pós-Parto Conforto', 'price': '29.90', 'cost': '12.00', 'cat': cat_lingerie, 'cols': ['Bege', 'Preto'], 'sz': ['P', 'M', 'G', 'GG']},
                    {'name': 'Kit 3 Calcinhas Gestante', 'price': '69.90', 'cost': '30.00', 'cat': cat_lingerie, 'cols': ['Listrado'], 'sz': ['P', 'M', 'G', 'GG']},
                    {'name': 'Top Amamentação Esportivo', 'price': '49.90', 'cost': '20.00', 'cat': cat_lingerie, 'cols': ['Cinza Mescla', 'Preto'], 'sz': ['M', 'G', 'GG']},

                    # --- PIJAMAS ---
                    {'name': 'Camisola Maternidade Algodão', 'price': '79.90', 'cost': '35.00', 'cat': cat_pijama, 'cols': ['Cinza Mescla', 'Rosa Bebê'], 'sz': ['P', 'M', 'G', 'GG']},
                    {'name': 'Pijama Americano Gestante', 'price': '119.90', 'cost': '55.00', 'cat': cat_pijama, 'cols': ['Azul Marinho', 'Vinho'], 'sz': ['P', 'M', 'G', 'GG']},
                ]

                count_created = 0
                count_existing = 0

                # 6. Loop criação
                for p in products_data:
                    product, created = Product.objects.get_or_create(
                        name=p['name'],
                        defaults={
                            'category': p['cat'],
                            'selling_price': Decimal(p['price']),
                            'description': f"Produto oficial da coleção {p['cat'].name}."
                        }
                    )

                    if created:
                        count_created += 1
                        ProductSupplier.objects.create(
                            product=product,
                            supplier=supplier,
                            cost_price=Decimal(p['cost'])
                        )

                        # Criar Variações
                        for c_name in p['cols']:
                            c_obj = color_objs.get(c_name)
                            for s_name in p['sz']:
                                s_obj = size_objs.get(s_name)
                                
                                ProductVariation.objects.create(
                                    product=product,
                                    color=c_obj,
                                    size=s_obj,
                                    stock=random.randint(5, 30),
                                    minimum_stock=3
                                )
                    else:
                        count_existing += 1
                        self.stdout.write(f"Já existe: {product.name}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro crítico: {e}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Concluído! {count_created} novos produtos criados. {count_existing} já existiam.'))