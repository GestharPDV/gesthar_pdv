# Plano de Ação Otimizado: Integração do Histórico de Compras no Perfil do Cliente

**Contexto para o Agente:**
Você está trabalhando no projeto `gesthar_pdv` (Django, PostgreSQL, Bootstrap 5). Sua tarefa é substituir os dados estáticos (placeholders) da tela de detalhes do cliente (`CustomerDetailView`) por dados dinâmicos reais, integrando o módulo de Clientes (`customer`) com o módulo de Vendas (`sales`). O sistema deve calcular os indicadores de consumo e listar as compras concluídas utilizando a relação reversa `purchases`.

---

## Fase 1: Preparação dos Dados (Camada de Views)
**Objetivo:** Processar os cálculos de consumo e extrair o histórico de vendas concluídas no backend antes de enviar para o template.

- [ ] **Passo 1.1:** Abra `customer/views.py` e localize a classe `CustomerDetailView`.
- [ ] **Passo 1.2:** Importe as funções de agregação do Django no topo do arquivo: `from django.db.models import Sum`. Importe também o modelo de vendas: `from sales.models import Sale`.
- [ ] **Passo 1.3:** Sobrescreva o método `get_context_data(self, **kwargs)` na `CustomerDetailView`.
- [ ] **Passo 1.4:** Dentro do `get_context_data`, recupere a instância do cliente com `customer = self.object`.
- [ ] **Passo 1.5:** Filtre o histórico real de compras:
    - Crie a variável `completed_purchases = customer.purchases.filter(status=Sale.Status.COMPLETED).order_by('-created_at')`.
- [ ] **Passo 1.6:** Calcule os indicadores financeiros usando `.aggregate()`:
    - **Total de Compras:** `completed_purchases.count()`.
    - **Valor Total Gasto:** `completed_purchases.aggregate(total=Sum('net_amount'))['total'] or Decimal('0.00')`.
    - **Média Mensal:** Divida o "Valor Total Gasto" pelos meses ativos do cliente (diferença entre a data atual e a data do primeiro pedido, com fallback para 1 se for o mesmo mês). *Alternativa simplificada:* `completed_purchases.aggregate(media=Avg('net_amount'))['media'] or Decimal('0.00')` (Ticket Médio).
- [ ] **Passo 1.7:** Injete essas variáveis no dicionário `context` (ex: `context['total_spent']`, `context['total_purchases']`, `context['purchase_history']`) e retorne o contexto atualizado.

---

## Fase 2: Integração de Interface (Camada de Templates)
**Objetivo:** Substituir os textos hardcoded pelo renderizador do Django (Jinja/Template Tags) para exibir os dados reais.

- [ ] **Passo 2.1:** Abra `customer/templates/customer/customer_detail.html`.
- [ ] **Passo 2.2:** Localize a seção de **Resumo de Compras** (Cards numéricos).
    - Substitua o texto `R$ 0,00` pela tag `R$ {{ total_spent|floatformat:2 }}`.
    - Substitua o texto `0` (Total de Compras) pela tag `{{ total_purchases }}`.
    - Substitua o texto `0,0` (Média Mensal) pela tag `R$ {{ monthly_average|floatformat:2 }}` (ou ticket médio, conforme definido na View).
- [ ] **Passo 2.3:** Localize a seção de **Histórico de Compras**. Remova o texto *"Histórico de compras será exibido após integração..."*.
- [ ] **Passo 2.4:** Implemente uma estrutura de Tabela HTML ou Lista (Bootstrap 5) iterando sobre a variável de contexto:
    - Use o laço `{% for sale in purchase_history %}`.
    - Para cada `sale`, exiba as colunas: Data (`{{ sale.created_at|date:"d/m/Y H:i" }}`), Código da Venda (`#{{ sale.id }}`), Status e Valor (`R$ {{ sale.net_amount|floatformat:2 }}`).
    - Utilize um bloco `{% empty %}` para exibir a mensagem *"Este cliente ainda não possui compras concluídas."* caso a lista esteja vazia.
    - Feche o laço com `{% endfor %}`.
- [ ] **Passo 2.5:** Adicione um botão ou link com ícone de "olho" na tabela para redirecionar o usuário para a tela de detalhes daquela venda (`{% url 'sales:sale-detail' sale.id %}`).

---

## Fase 3: Segurança e Testes
**Objetivo:** Garantir que o cálculo não quebre caso o cliente seja novo e que a segurança do banco seja mantida.

- [ ] **Passo 3.1:** Em `customer/tests.py`, adicione um teste unitário para a `CustomerDetailView`.
- [ ] **Passo 3.2:** No teste, crie um Cliente e associe a ele 2 Vendas Concluídas e 1 Venda em Rascunho.
- [ ] **Passo 3.3:** Verifique via `response.context` se o `total_purchases` é igual a 2 (ignorando o rascunho) e se o valor total corresponde apenas à soma das concluídas.

---

### Considerações de Engenharia:
1. **Performance da Query:** Na View, ao buscar as compras, utilize `.prefetch_related('items')` caso precise exibir a quantidade de produtos comprados em cada linha do histórico, evitando problemas de "N+1 Queries".
2. **Separação de Contexto:** Vendas canceladas (`CANCELED`) não devem entrar no cálculo do "Valor Total Gasto" para não distorcer o LTV (Lifetime Value) do cliente. O filtro estrito por `status=Sale.Status.COMPLETED` é mandatório.