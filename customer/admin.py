from django.contrib import admin
from .models import Customer, Address


class AddressInline(admin.TabularInline):
    """
    Inline para exibir e editar endereços diretamente na página do cliente.
    """
    model = Address
    extra = 1  # Número de formulários vazios extras
    fields = ['cep', 'state', 'city', 'neighborhood', 'street', 'number', 'complement']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """
    Configuração do Django Admin para o modelo Customer.
    """
    list_display = [
        'name',
        'cpf_cnpj',
        'email',
        'phone',
        'baby_due_date',
        'created_at'
    ]
    
    list_filter = [
        'created_at',
        'baby_due_date',
        'updated_at'
    ]
    
    search_fields = [
        'name',
        'cpf_cnpj',
        'email',
        'phone'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Dados Pessoais', {
            'fields': ('name', 'cpf_cnpj', 'birth_date', 'baby_due_date')
        }),
        ('Contato', {
            'fields': ('email', 'phone')
        }),
        ('Preferências', {
            'fields': ('size_preferences', 'note')
        }),
        ('Informações do Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [AddressInline]
    
    date_hierarchy = 'created_at'
    
    ordering = ['-created_at']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """
    Configuração do Django Admin para o modelo Address.
    """
    list_display = [
        'customer',
        'street',
        'number',
        'neighborhood',
        'city',
        'state',
        'cep'
    ]
    
    list_filter = [
        'state',
        'city'
    ]
    
    search_fields = [
        'customer__name',
        'street',
        'neighborhood',
        'city',
        'cep'
    ]
    
    autocomplete_fields = ['customer']
    
    fieldsets = (
        ('Informações do Endereço', {
            'fields': ('customer', 'cep', 'state', 'city', 'neighborhood', 'street', 'number', 'complement')
        }),
    )
