# product/management/commands/populate_demo.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import random

from product.models import (
    Product, Category, Color, Size, Supplier, 
    ProductVariation, ProductSupplier
)
from user.models import UserGesthar
from customer.models import Customer, Address
from sales.models import Sale, SaleItem, SalePayment, CashRegister
from stock.models import StockMovement
from stock.services import remove_stock


class Command(BaseCommand):
    help = 'Popula o banco com dados completos para demonstração do PDV de vestuário gestante'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpa dados existentes antes de popular',
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando população do banco para apresentação...')

        if options['clear']:
            self.stdout.write('⚠️  Limpando dados existentes...')
            # Não vamos deletar tudo, apenas avisar
            self.stdout.write(self.style.WARNING('Use com cuidado em produção!'))

        try:
            with transaction.atomic():
                # 1. CRIAR CATEGORIAS
                self.stdout.write('📁 Criando categorias...')
                categories = self._create_categories()
                
                # 2. CRIAR CORES E TAMANHOS
                self.stdout.write('🎨 Criando cores e tamanhos...')
                colors, sizes = self._create_colors_and_sizes()
                
                # 3. CRIAR FORNECEDORES
                self.stdout.write('🏭 Criando fornecedores...')
                suppliers = self._create_suppliers()
                
                # 4. CRIAR PRODUTOS COM VARIAÇÕES
                self.stdout.write('👕 Criando produtos e variações...')
                products = self._create_products(categories, colors, sizes, suppliers)
                
                # 5. CRIAR USUÁRIOS (VENDEDORES)
                self.stdout.write('👤 Criando usuários/vendedores...')
                users = self._create_users()
                
                # 6. CRIAR CLIENTES
                self.stdout.write('👥 Criando clientes...')
                customers = self._create_customers()
                
                # 7. CRIAR SESSÕES DE CAIXA
                self.stdout.write('💰 Criando sessões de caixa...')
                cash_registers = self._create_cash_registers(users)
                
                # 8. CRIAR VENDAS COMPLETAS
                self.stdout.write('🛒 Criando vendas...')
                sales = self._create_sales(users, customers, cash_registers, products)
                
                self.stdout.write(self.style.SUCCESS(
                    f'\n✅ População concluída com sucesso!\n'
                    f'   📦 {len(products)} produtos criados\n'
                    f'   👤 {len(users)} usuários criados\n'
                    f'   👥 {len(customers)} clientes criados\n'
                    f'   💰 {len(cash_registers)} sessões de caixa criadas\n'
                    f'   🛒 {len(sales)} vendas criadas\n'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro crítico: {e}'))
            import traceback
            traceback.print_exc()
            raise

    def _create_categories(self):
        categories_data = [
            {'name': 'Moda Gestante', 'description': 'Roupas casuais e sociais para gestantes'},
            {'name': 'Lingerie Maternidade', 'description': 'Sutiãs, calcinhas e cintas'},
            {'name': 'Pijamas e Camisolas', 'description': 'Linha noite para gestante e amamentação'},
            {'name': 'Acessórios', 'description': 'Bolsas, sapatos e acessórios para gestantes'},
        ]
        
        categories = []
        for cat_data in categories_data:
            cat, _ = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories.append(cat)
        return categories

    def _create_colors_and_sizes(self):
        colors_list = [
            'Preto', 'Branco', 'Bege', 'Rosa Bebê', 'Azul Marinho',
            'Cinza Mescla', 'Vinho', 'Verde Militar', 'Estampado Floral',
            'Listrado', 'Nude', 'Coral', 'Lavanda'
        ]
        
        sizes_list = ['P', 'M', 'G', 'GG', 'XG', '38', '40', '42', '44', '46', '48']
        
        colors = {}
        for c in colors_list:
            color, _ = Color.objects.get_or_create(name=c)
            colors[c] = color
        
        sizes = {}
        for s in sizes_list:
            size, _ = Size.objects.get_or_create(name=s)
            sizes[s] = size
        
        return colors, sizes

    def _create_suppliers(self):
        suppliers_data = [
            'Fornecedor Gestante SP',
            'Moda Materna Ltda',
            'Confecções Belly',
            'Atacado Maternidade',
        ]
        
        suppliers = []
        for name in suppliers_data:
            supplier, _ = Supplier.objects.get_or_create(name=name)
            suppliers.append(supplier)
        return suppliers

    def _create_products(self, categories, colors, sizes, suppliers):
        products_data = [
            # MODA GESTANTE
            {
                'name': 'Vestido Midi Canelado',
                'price': Decimal('89.90'),
                'cost': Decimal('45.00'),
                'category': categories[0],
                'colors': ['Preto', 'Vinho', 'Cinza Mescla', 'Bege'],
                'sizes': ['P', 'M', 'G', 'GG'],
                'description': 'Vestido confortável com tecido canelado, ideal para o dia a dia.'
            },
            {
                'name': 'Calça Jeans Cós Elástico',
                'price': Decimal('129.90'),
                'cost': Decimal('60.00'),
                'category': categories[0],
                'colors': ['Azul Marinho'],
                'sizes': ['38', '40', '42', '44', '46'],
                'description': 'Calça jeans com cós elástico ajustável para conforto durante a gestação.'
            },
            {
                'name': 'Bata Soltinha Viscose',
                'price': Decimal('79.90'),
                'cost': Decimal('35.00'),
                'category': categories[0],
                'colors': ['Branco', 'Estampado Floral', 'Rosa Bebê'],
                'sizes': ['P', 'M', 'G', 'GG'],
                'description': 'Bata leve e soltinha em viscose, perfeita para o verão.'
            },
            {
                'name': 'Shorts Gestante Linho',
                'price': Decimal('89.90'),
                'cost': Decimal('40.00'),
                'category': categories[0],
                'colors': ['Bege', 'Preto', 'Verde Militar'],
                'sizes': ['P', 'M', 'G', 'GG'],
                'description': 'Shorts em linho natural, confortável e elegante.'
            },
            {
                'name': 'Legging Gestante Básica',
                'price': Decimal('59.90'),
                'cost': Decimal('25.00'),
                'category': categories[0],
                'colors': ['Preto', 'Cinza Mescla', 'Azul Marinho'],
                'sizes': ['P', 'M', 'G', 'GG', 'XG'],
                'description': 'Legging básica com tecido elástico e confortável.'
            },
            {
                'name': 'Macacão Longo Malha',
                'price': Decimal('119.90'),
                'cost': Decimal('55.00'),
                'category': categories[0],
                'colors': ['Preto', 'Verde Militar', 'Vinho'],
                'sizes': ['M', 'G', 'GG'],
                'description': 'Macacão longo em malha, peça única e versátil.'
            },
            {
                'name': 'Blusa Amamentação Transpassada',
                'price': Decimal('69.90'),
                'cost': Decimal('30.00'),
                'category': categories[0],
                'colors': ['Rosa Bebê', 'Branco', 'Listrado', 'Nude'],
                'sizes': ['P', 'M', 'G', 'GG'],
                'description': 'Blusa com abertura discreta para amamentação.'
            },
            {
                'name': 'Vestido Longo Estampado',
                'price': Decimal('149.90'),
                'cost': Decimal('70.00'),
                'category': categories[0],
                'colors': ['Estampado Floral', 'Listrado'],
                'sizes': ['P', 'M', 'G'],
                'description': 'Vestido longo com estampa exclusiva, ideal para ocasiões especiais.'
            },
            {
                'name': 'Cardigan Alongado Tricô',
                'price': Decimal('99.90'),
                'cost': Decimal('45.00'),
                'category': categories[0],
                'colors': ['Bege', 'Cinza Mescla', 'Preto', 'Lavanda'],
                'sizes': ['P', 'M', 'G'],
                'description': 'Cardigan em tricô, peça essencial para o inverno.'
            },
            {
                'name': 'Jardineira Jeans Gestante',
                'price': Decimal('159.90'),
                'cost': Decimal('75.00'),
                'category': categories[0],
                'colors': ['Azul Marinho'],
                'sizes': ['38', '40', '42', '44'],
                'description': 'Jardineira em jeans com ajuste para gestantes.'
            },
            # LINGERIE
            {
                'name': 'Sutiã Amamentação Renda',
                'price': Decimal('59.90'),
                'cost': Decimal('25.00'),
                'category': categories[1],
                'colors': ['Branco', 'Bege', 'Preto', 'Rosa Bebê', 'Nude'],
                'sizes': ['M', 'G', 'GG'],
                'description': 'Sutiã com abertura frontal para amamentação, em renda delicada.'
            },
            {
                'name': 'Cinta Pós-Parto Modeladora',
                'price': Decimal('89.90'),
                'cost': Decimal('40.00'),
                'category': categories[1],
                'colors': ['Bege', 'Preto'],
                'sizes': ['P', 'M', 'G', 'GG'],
                'description': 'Cinta modeladora para uso pós-parto, oferece suporte e conforto.'
            },
            {
                'name': 'Kit 3 Calcinhas Gestante',
                'price': Decimal('69.90'),
                'cost': Decimal('30.00'),
                'category': categories[1],
                'colors': ['Listrado', 'Branco', 'Bege'],
                'sizes': ['P', 'M', 'G', 'GG'],
                'description': 'Kit com 3 calcinhas confortáveis para gestantes.'
            },
            # PIJAMAS
            {
                'name': 'Camisola Maternidade Algodão',
                'price': Decimal('79.90'),
                'cost': Decimal('35.00'),
                'category': categories[2],
                'colors': ['Cinza Mescla', 'Rosa Bebê', 'Lavanda'],
                'sizes': ['P', 'M', 'G', 'GG'],
                'description': 'Camisola em algodão 100%, confortável para dormir e amamentar.'
            },
            {
                'name': 'Pijama Americano Gestante',
                'price': Decimal('119.90'),
                'cost': Decimal('55.00'),
                'category': categories[2],
                'colors': ['Azul Marinho', 'Vinho', 'Estampado Floral'],
                'sizes': ['P', 'M', 'G', 'GG'],
                'description': 'Pijama estilo americano, conjunto completo e confortável.'
            },
        ]
        
        products = []
        for p_data in products_data:
            product, created = Product.objects.get_or_create(
                name=p_data['name'],
                defaults={
                    'category': p_data['category'],
                    'selling_price': p_data['price'],
                    'description': p_data.get('description', '')
                }
            )
            
            if created:
                # Adicionar fornecedor
                supplier = random.choice(suppliers)
                ProductSupplier.objects.create(
                    product=product,
                    supplier=supplier,
                    cost_price=p_data['cost']
                )
                
                # Criar variações com estoque variado
                for color_name in p_data['colors']:
                    color = colors.get(color_name)
                    if not color:
                        continue
                    
                    for size_name in p_data['sizes']:
                        size = sizes.get(size_name)
                        if not size:
                            continue
                        
                        # Estoque variado: alguns produtos com estoque baixo, outros alto
                        stock_qty = random.choice([
                            random.randint(0, 2),  # Estoque baixo (20% chance)
                            random.randint(3, 10),  # Estoque médio (50% chance)
                            random.randint(15, 50),  # Estoque alto (30% chance)
                        ])
                        
                        ProductVariation.objects.create(
                            product=product,
                            color=color,
                            size=size,
                            stock=stock_qty,
                            minimum_stock=3
                        )
            
            products.append(product)
        
        return products

    def _create_users(self):
        users_data = [
            {
                'email': 'maria.silva@gesthar.com',
                'first_name': 'Maria',
                'last_name': 'Silva',
                'cpf': '12345678901',
                'role': 'Gerente de Vendas',
                'phone_number': '(11) 98765-4321',
            },
            {
                'email': 'ana.costa@gesthar.com',
                'first_name': 'Ana',
                'last_name': 'Costa',
                'cpf': '23456789012',
                'role': 'Vendedora',
                'phone_number': '(11) 98765-4322',
            },
            {
                'email': 'julia.oliveira@gesthar.com',
                'first_name': 'Júlia',
                'last_name': 'Oliveira',
                'cpf': '34567890123',
                'role': 'Vendedora',
                'phone_number': '(11) 98765-4323',
            },
        ]
        
        users = []
        for u_data in users_data:
            user, created = UserGesthar.objects.get_or_create(
                email=u_data['email'],
                defaults={
                    'first_name': u_data['first_name'],
                    'last_name': u_data['last_name'],
                    'cpf': u_data['cpf'],
                    'role': u_data['role'],
                    'phone_number': u_data['phone_number'],
                    'is_staff': True,
                    'is_active': True,
                }
            )
            if created:
                user.set_password('demo123')  # Senha padrão para demo
                user.save()
            users.append(user)
        
        return users

    def _create_customers(self):
        customers_data = [
            {
                'name': 'Patrícia Santos',
                'cpf_cnpj': '11122233344',
                'email': 'patricia.santos@email.com',
                'phone': '(11) 98765-1111',
                'baby_due_date': timezone.now().date() + timedelta(days=60),
                'size_preferences': 'M, G',
                'address': {
                    'cep': '01310-100',
                    'state': 'SP',
                    'city': 'São Paulo',
                    'neighborhood': 'Bela Vista',
                    'street': 'Av. Paulista',
                    'number': '1000',
                    'complement': 'Apto 101'
                }
            },
            {
                'name': 'Fernanda Lima',
                'cpf_cnpj': '22233344455',
                'email': 'fernanda.lima@email.com',
                'phone': '(11) 98765-2222',
                'baby_due_date': timezone.now().date() + timedelta(days=90),
                'size_preferences': 'G, GG',
                'address': {
                    'cep': '04547-130',
                    'state': 'SP',
                    'city': 'São Paulo',
                    'neighborhood': 'Vila Olímpia',
                    'street': 'Rua Funchal',
                    'number': '200',
                    'complement': ''
                }
            },
            {
                'name': 'Camila Rodrigues',
                'cpf_cnpj': '33344455566',
                'email': 'camila.rodrigues@email.com',
                'phone': '(11) 98765-3333',
                'baby_due_date': timezone.now().date() + timedelta(days=120),
                'size_preferences': 'P, M',
                'address': {
                    'cep': '05433-000',
                    'state': 'SP',
                    'city': 'São Paulo',
                    'neighborhood': 'Pinheiros',
                    'street': 'Rua dos Pinheiros',
                    'number': '500',
                    'complement': 'Casa'
                }
            },
            {
                'name': 'Larissa Ferreira',
                'cpf_cnpj': '44455566677',
                'email': 'larissa.ferreira@email.com',
                'phone': '(11) 98765-4444',
                'baby_due_date': timezone.now().date() + timedelta(days=30),
                'size_preferences': 'M',
                'address': {
                    'cep': '01234-567',
                    'state': 'SP',
                    'city': 'São Paulo',
                    'neighborhood': 'Centro',
                    'street': 'Rua Augusta',
                    'number': '1500',
                    'complement': 'Loja 5'
                }
            },
            {
                'name': 'Beatriz Alves',
                'cpf_cnpj': '55566677788',
                'email': 'beatriz.alves@email.com',
                'phone': '(11) 98765-5555',
                'baby_due_date': timezone.now().date() + timedelta(days=150),
                'size_preferences': 'G',
                'address': {
                    'cep': '04038-001',
                    'state': 'SP',
                    'city': 'São Paulo',
                    'neighborhood': 'Vila Mariana',
                    'street': 'Av. Brigadeiro Luís Antônio',
                    'number': '3000',
                    'complement': 'Apto 202'
                }
            },
        ]
        
        customers = []
        for c_data in customers_data:
            customer, created = Customer.objects.get_or_create(
                cpf_cnpj=c_data['cpf_cnpj'],
                defaults={
                    'name': c_data['name'],
                    'email': c_data['email'],
                    'phone': c_data['phone'],
                    'baby_due_date': c_data['baby_due_date'],
                    'size_preferences': c_data['size_preferences'],
                }
            )
            
            if created and 'address' in c_data:
                Address.objects.create(
                    customer=customer,
                    **c_data['address']
                )
            
            customers.append(customer)
        
        return customers

    def _create_cash_registers(self, users):
        cash_registers = []
        
        # Criar algumas sessões fechadas (histórico)
        for i in range(3):
            user = random.choice(users)
            register = CashRegister.objects.create(
                user=user,
                opening_balance=Decimal('100.00'),
                closing_balance=Decimal('100.00') + Decimal(random.randint(500, 2000)),
                opened_at=timezone.now() - timedelta(days=random.randint(1, 7)),
                closed_at=timezone.now() - timedelta(days=random.randint(1, 7)) + timedelta(hours=8),
                status=CashRegister.Status.CLOSED
            )
            cash_registers.append(register)
        
        # Criar uma sessão aberta (atual)
        current_user = users[0]
        open_register = CashRegister.objects.create(
            user=current_user,
            opening_balance=Decimal('100.00'),
            opened_at=timezone.now() - timedelta(hours=2),
            status=CashRegister.Status.OPEN
        )
        cash_registers.append(open_register)
        
        return cash_registers

    def _create_sales(self, users, customers, cash_registers, products):
        sales = []
        
        # Buscar variações disponíveis
        variations = list(ProductVariation.objects.filter(is_active=True, stock__gt=0))
        
        if not variations:
            self.stdout.write(self.style.WARNING('⚠️  Nenhuma variação com estoque encontrada!'))
            return sales
        
        # Criar vendas concluídas (histórico)
        closed_registers = [cr for cr in cash_registers if cr.status == CashRegister.Status.CLOSED]
        open_register = next((cr for cr in cash_registers if cr.status == CashRegister.Status.OPEN), None)
        
        # Vendas antigas (concluídas)
        for i in range(8):
            if not closed_registers:
                break
            
            register = random.choice(closed_registers)
            user = register.user
            customer = random.choice(customers) if random.random() > 0.3 else None  # 30% sem cliente
            
            # Criar venda como DRAFT primeiro
            created_time = register.opened_at + timedelta(minutes=random.randint(30, 480))
            sale = Sale.objects.create(
                user=user,
                customer=customer,
                cash_register_session=register,
                status=Sale.Status.DRAFT,
                created_at=created_time,
            )
            
            # Adicionar itens (apenas variações com estoque suficiente)
            num_items = random.randint(1, 5)
            available_variations = [v for v in variations if v.stock > 0]
            if not available_variations:
                sale.delete()
                continue
                
            selected_variations = random.sample(
                available_variations, 
                min(num_items, len(available_variations))
            )
            
            for variation in selected_variations:
                quantity = random.randint(1, min(3, variation.stock))  # Não exceder estoque
                unit_price = variation.product.selling_price
                discount = Decimal('0.00') if random.random() > 0.2 else Decimal(str(random.randint(5, 20)))  # 20% com desconto
                
                SaleItem.objects.create(
                    sale=sale,
                    variation=variation,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount=discount,
                )
            
            sale.calculate_totals()
            
            # Adicionar pagamentos
            net_amount = sale.net_amount
            payment_methods = [
                SalePayment.Method.DINHEIRO,
                SalePayment.Method.PIX,
                SalePayment.Method.CARTAO_DEBITO,
                SalePayment.Method.CARTAO_CREDITO,
            ]
            
            # Pagamento único ou múltiplo
            if random.random() > 0.3:  # 70% pagamento único
                method = random.choice(payment_methods)
                SalePayment.objects.create(
                    sale=sale,
                    method=method,
                    amount=net_amount
                )
            else:  # 30% pagamento múltiplo (ex: parte em dinheiro, parte no cartão)
                amount1 = net_amount * Decimal('0.6')
                amount2 = net_amount - amount1
                SalePayment.objects.create(
                    sale=sale,
                    method=SalePayment.Method.DINHEIRO,
                    amount=amount1
                )
                SalePayment.objects.create(
                    sale=sale,
                    method=random.choice([SalePayment.Method.PIX, SalePayment.Method.CARTAO_DEBITO]),
                    amount=amount2
                )
            
            # Para vendas antigas, fazer baixa de estoque manualmente e marcar como concluída
            # (não podemos usar complete_sale() porque o caixa está fechado)
            try:
                # Baixar estoque manualmente para cada item
                for item in sale.items.all():
                    remove_stock(
                        product_variation_id=item.variation.pk,
                        quantity=item.quantity,
                        user=user,
                        movement_type=StockMovement.MovementType.VENDA,
                        notes=f"Venda PDV #{sale.pk} (histórico)"
                    )
                
                # Marcar venda como concluída
                completed_time = created_time + timedelta(minutes=random.randint(5, 30))
                sale.status = Sale.Status.COMPLETED
                sale.completed_at = completed_time
                sale.change_amount = sale.change_preview
                sale.save()
                
                sales.append(sale)
            except Exception as e:
                # Se não conseguir finalizar (ex: falta estoque), deleta a venda
                self.stdout.write(self.style.WARNING(f'⚠️  Não foi possível finalizar venda: {e}'))
                sale.delete()
        
        # Criar algumas vendas em rascunho (para demonstrar o fluxo)
        if open_register:
            for i in range(2):
                user = open_register.user
                customer = random.choice(customers) if random.random() > 0.5 else None
                
                sale = Sale.objects.create(
                    user=user,
                    customer=customer,
                    cash_register_session=open_register,
                    status=Sale.Status.DRAFT,
                )
                
                # Adicionar alguns itens
                num_items = random.randint(1, 3)
                selected_variations = random.sample(variations, min(num_items, len(variations)))
                
                for variation in selected_variations:
                    quantity = random.randint(1, 2)
                    unit_price = variation.product.selling_price
                    
                    SaleItem.objects.create(
                        sale=sale,
                        variation=variation,
                        quantity=quantity,
                        unit_price=unit_price,
                    )
                
                sale.calculate_totals()
                sales.append(sale)
        
        return sales