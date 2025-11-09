# Módulo de Cadastro de Clientes

## 📋 Sumário

O módulo de clientes do sistema Gesthar permite o cadastro completo de clientes de uma loja de roupas para gestantes, incluindo dados pessoais, endereços e preparação para histórico de compras.

## ✅ Funcionalidades Implementadas

### 1. Cadastro de Clientes

**Dados cadastrados:**
- Nome completo
- CPF/CNPJ (com validação)
- Data de nascimento
- Email (único)
- Telefone/WhatsApp
- Data prevista do parto (específico para gestantes)
- Preferências de tamanho
- Observações gerais
- Múltiplos endereços

### 2. Validação de CPF/CNPJ

- Aceita CPF (11 dígitos) ou CNPJ (14 dígitos)
- Validação de dígitos verificadores
- Remove automaticamente caracteres especiais (pontos, traços, barras)
- Implementado em `customer/validators.py`

### 3. CRUD Completo

**Views implementadas:**
- `CustomerListView` - Listagem com busca e paginação
- `CustomerCreateView` - Cadastro de cliente + endereços
- `CustomerDetailView` - Visualização detalhada + histórico
- `CustomerUpdateView` - Edição de dados
- `CustomerDeleteView` - Exclusão com confirmação

**URLs configuradas:**
- `/clientes/` - Listagem
- `/clientes/novo/` - Cadastro
- `/clientes/<id>/` - Detalhes
- `/clientes/<id>/editar/` - Edição
- `/clientes/<id>/deletar/` - Exclusão

### 4. Templates

Todos os templates herdam de `global/sidebar.html` e seguem o padrão visual do sistema:

- `customer_list.html` - Lista paginada com busca
- `customer_form.html` - Formulário com formset de endereços
- `customer_detail.html` - Detalhes completos + histórico
- `customer_confirm_delete.html` - Confirmação de exclusão

### 5. Django Admin

Configuração completa no admin do Django:
- `CustomerAdmin` com inline de endereços
- Filtros por data de cadastro e data prevista do parto
- Busca por nome, CPF/CNPJ, email e telefone
- Campos readonly para timestamps

### 6. Integração com Sidebar

Os links do módulo de clientes foram adicionados ao menu lateral:
- CADASTRAR CLIENTE
- CONSULTAR CLIENTES

## 🔄 Preparação para Histórico de Compras

O modelo `Customer` possui métodos preparatórios que retornam dados placeholder até a integração com o módulo de vendas/PDV:

```python
# Métodos implementados (retornam dados vazios/zero)
customer.get_purchase_history()      # Lista de compras
customer.get_total_spent()           # Valor total gasto
customer.get_purchase_frequency()    # Frequência de compras
customer.get_favorite_products()     # Produtos preferidos
```

**Na página de detalhes do cliente (`customer_detail.html`), já está implementada a estrutura para exibir:**
- Resumo de compras (valor total, total de compras, média mensal)
- Histórico de compras (tabela preparada)
- Produtos favoritos (seção preparada)

Quando o módulo de vendas estiver disponível, basta:
1. Atualizar os métodos no modelo `Customer` para consultar as vendas reais
2. Os templates já exibirão os dados automaticamente

## 📁 Estrutura de Arquivos

```
customer/
├── migrations/
│   ├── 0001_initial.py
│   └── 0002_update_customer_fields.py
├── templates/
│   └── customer/
│       ├── customer_list.html
│       ├── customer_form.html
│       ├── customer_detail.html
│       └── customer_confirm_delete.html
├── __init__.py
├── admin.py          # Configuração do Django Admin
├── apps.py
├── forms.py          # CustomerForm e AddressFormSet
├── models.py         # Customer e Address
├── urls.py           # Rotas do módulo
├── validators.py     # Validação de CPF/CNPJ
├── views.py          # Views CRUD
└── README.md         # Esta documentação
```

## 🔐 Controle de Acesso

Todas as views exigem autenticação (`LoginRequiredMixin`).

## 🎨 Padrão Visual

O módulo segue a paleta de cores do sistema:
- **Principal:** #FF7690 (Rosa)
- **Secundário:** #F1F0BE (Amarelo claro)
- **Fundo:** #F9FAFB (Cinza claro)
- **Destaque:** #F7E8EB (Rosa claro)

## 🚀 Próximos Passos (Opcional)

As seguintes funcionalidades foram definidas como **opcionais** nos requisitos:

1. **Comunicação com cliente:**
   - Envio de ofertas por email/SMS
   - Lembretes de aniversário
   - Notificações de chegada de produtos

2. **Integração com módulo de vendas:**
   - Histórico real de compras
   - Cálculo de valor total gasto
   - Frequência de compras
   - Identificação de produtos preferidos

## 📝 Observações Técnicas

- Utiliza `widget_tweaks` para estilização de formulários
- FormSet inline para múltiplos endereços
- Validação customizada de CPF/CNPJ
- Campos de busca por nome, CPF/CNPJ, email e telefone
- Paginação de 20 itens por página
- Messages framework para feedback ao usuário

