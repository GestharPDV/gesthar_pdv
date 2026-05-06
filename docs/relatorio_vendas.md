### Arquivo: `/docs/relatorio-vendas.md`

# Plano de Ação Otimizado para Claude Code: Relatórios de Vendas (Administrativo)

**Contexto para o Agente:**
Você está trabalhando no projeto `gesthar_pdv` (Django, PostgreSQL, Bootstrap 5). Sua tarefa é implementar o Módulo de Relatórios de Vendas voltado exclusivamente para os administradores da empresa. A implementação deve seguir a modelagem do banco de dados atual contida em `sales/models.py`, utilizando as tabelas `Sale`, `SaleItem`, e `SalePayment`. 

---

## Fase 1: Camada de Serviços (Consultas ORM)
**Objetivo:** Criar funções precisas para extrair os indicadores financeiros e operacionais de vendas.

* **Passo 1.1:** Crie ou abra o arquivo `sales/services.py`. Importe os modelos `Sale`, `SaleItem` e `SalePayment`.
* **Passo 1.2:** Crie a função `get_total_revenue(start_date, end_date)`: Calcule o faturamento total somando o campo `net_amount` das vendas cujo status seja `COMPLETED`.
* **Passo 1.3:** Crie a função `get_revenue_by_payment_method(start_date, end_date)`: Agrupe e some o campo `amount` da tabela `SalePayment` filtrando por vendas com status `COMPLETED`, agrupado pelo campo `method`.
* **Passo 1.4:** Crie a função `get_sales_by_user(start_date, end_date)`: Agrupe o faturamento líquido (`net_amount`) e a contagem de vendas concluídas pelo campo `user` (vendedor/operador).
* **Passo 1.5:** Crie a função `get_top_selling_items(start_date, end_date)`: Agrupe a quantidade vendida consultando a tabela `SaleItem` associada a vendas `COMPLETED`, retornando as variações mais vendidas.
* **Passo 1.6:** Crie a função `get_total_discounts(start_date, end_date)`: Some o campo `discount_amount` das vendas `COMPLETED` para acompanhamento de métricas de desconto.

---

## Fase 2: Controladores e Estrutura de Dados (Views e URLs)
**Objetivo:** Criar a view de visualização, garantindo restrição de acesso e preparação de dados no formato JSON para gráficos.

* **Passo 2.1:** Em `sales/views.py`, crie a classe `SalesReportView`. Ela deve herdar de `LoginRequiredMixin`, `AdminRequiredMixin` (para garantir que apenas administradores acessem) e `TemplateView`. Defina o `template_name` como `sales/report_sales.html`.
* **Passo 2.2:** No método `get_context_data`, capture os parâmetros de filtro (Data Inicial, Data Final) via `self.request.GET`.
* **Passo 2.3:** Utilize as funções da camada de serviços para buscar os dados. Formate os dados de "Receita por Método de Pagamento" e "Vendas por Operador" em dicionários e os converta para JSON usando `json.dumps()`. Injete no contexto (ex: `context['payment_chart_json']`, `context['user_chart_json']`).
* **Passo 2.4:** Injete no contexto os KPIs globais: Faturamento Total, Total de Descontos e Número de Vendas Concluídas.
* **Passo 2.5:** Em `sales/urls.py`, registre a rota `path('relatorios/vendas/', views.SalesReportView.as_view(), name='report-sales')`.

---

## Fase 3: Interface de Usuário, Gráficos e Exportação PDF (Templates)
**Objetivo:** Construir o Dashboard analítico responsivo e implementar a funcionalidade de exportação de relatório consolidado.

* **Passo 3.1:** Crie o arquivo `sales/templates/sales/report_sales.html` estendendo `base/base.html`.
* **Passo 3.2:** No bloco `{% block scripts %}`, importe as bibliotecas de visualização:
    * `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`
    * `<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>`
* **Passo 3.3:** Crie a estrutura de filtros por período de data e adicione o botão de exportação: `<button id="btn-export-pdf" class="btn btn-primary"><i class="fas fa-file-pdf"></i> Exportar Relatório</button>`.
* **Passo 3.4:** Adicione uma `div` encapsuladora com o `id="report-content"`.
* **Passo 3.5:** Desenvolva os componentes visuais internos:
    * Cards superiores para os KPIs (Faturamento Líquido, Total de Descontos, Volume de Vendas).
    * Elemento `<canvas id="paymentChart"></canvas>` para o gráfico de pizza (Métodos de Pagamento).
    * Elemento `<canvas id="userChart"></canvas>` para o gráfico de barras (Vendas por Operador).
    * Tabela com o ranking dos Produtos mais vendidos (Top 10).
* **Passo 3.6:** Escreva o Javascript interno para instanciar os gráficos do `Chart.js`, aplicando `|safe` nas variáveis de contexto. Defina `animation: false` nas configurações para permitir exportação limpa.
* **Passo 3.7:** Acople o script de geração PDF ao botão, exportando apenas o bloco `#report-content`.

---

## Fase 4: Integração de Navegação
**Objetivo:** Disponibilizar o atalho no menu do painel.

* **Passo 4.1:** Abra `base/templates/base/sidebar.html`.
* **Passo 4.2:** Dentro de um bloco condicional `{% if user.role == 'ADMIN' %}`, insira um novo item de menu apontando para `href="{% url 'sales:report-sales' %}"`.

---

## Fase 5: Validação e Testes
**Objetivo:** Garantir a funcionalidade das consultas e a segurança das rotas.

* **Passo 5.1:** Em `sales/tests/test_views.py` (ou arquivo equivalente respeitando a organização atual sem conflitos), crie um teste para verificar o bloqueio de acesso: Autentique-se como usuário `VENDEDOR` e confira se a rota `sales:report-sales` retorna `HTTP 403 Forbidden`.
* **Passo 5.2:** Crie um teste validando se, ao acessar como `ADMIN`, a rota retorna `HTTP 200 OK` e se o contexto da página inclui as chaves `payment_chart_json` e as totalizações matemáticas correspondentes às vendas mockadas no banco de testes.