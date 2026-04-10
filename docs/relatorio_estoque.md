# Plano de Ação para Claude Code: Relatórios de Estoque com Gráficos e Exportação PDF (RF016)

**Contexto para o Agente:**
Você está trabalhando no projeto `gesthar_pdv` (Django, PostgreSQL, Bootstrap 5). Sua tarefa é implementar o Módulo de Relatórios de Estoque com recursos visuais (Gráficos) e capacidade de exportação para PDF preservando a interface visual já definida em modulos anteriores.

---

## Fase 1: Camada de Serviços (Consultas ORM)
**Objetivo:** Criar funções para extrair os indicadores de estoque.

- [ ] **Passo 1.1:** Abra `stock/services.py` (crie se não existir). Importe os modelos necessários.
- [ ] **Passo 1.2:** Crie `get_inventory_valuation()`: Calcule o valor total do estoque multiplicando `stock` por `selling_price` (via `annotate` e `Sum`).
- [ ] **Passo 1.3:** Crie `get_low_stock_products()`: Filtre produtos onde `stock <= minimum_stock` e `is_active=True`.
- [ ] **Passo 1.4:** Crie `get_top_selling_products(start_date, end_date)`: Retorne os produtos mais vendidos no período (agrupando por produto e somando a quantidade do `SaleItem`).
- [ ] **Passo 1.5:** Crie `get_stagnant_products(days=30)`: Identifique produtos sem movimentação de saída nos últimos X dias.

---

## Fase 2: Controladores e Estrutura de Dados (Views e URLs)
**Objetivo:** Criar a view e preparar os dados no formato correto (JSON) para renderização dos gráficos no frontend.

- [ ] **Passo 2.1:** Em `stock/views.py`, crie a classe `StockReportView` herdando de `LoginRequiredMixin` e `TemplateView` (template: `stock/report_stock.html`).
- [ ] **Passo 2.2:** No método `get_context_data`, processe os filtros (Data Inicial, Data Final, Categoria) a partir de `self.request.GET`.
- [ ] **Passo 2.3:** Formate os dados de "Produtos Mais Vendidos" e "Entradas vs Saídas" em dicionários e converta-os para strings JSON (usando `import json` e `json.dumps()`). Injete essas strings no contexto (ex: `context['chart_labels_json']`, `context['chart_data_json']`) para que o Javascript possa lê-los no template.
- [ ] **Passo 2.4:** Em `stock/urls.py`, registre a rota `path('relatorios/estoque/', views.StockReportView.as_view(), name='report-stock')`.

---

## Fase 3: Interface de Usuário, Gráficos e Exportação PDF (Templates)
**Objetivo:** Construir o Dashboard responsivo, renderizar os gráficos e implementar o motor de exportação PDF via client-side.

- [ ] **Passo 3.1:** Crie `stock/templates/stock/report_stock.html` estendendo `base/base.html`.
- [ ] **Passo 3.2:** No bloco de scripts (`{% block scripts %}`), adicione as CDNs do Chart.js e do html2pdf:
  - `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`
  - `<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>`
- [ ] **Passo 3.3:** Crie o botão de exportação no topo da página: `<button id="btn-export-pdf" class="btn btn-danger"><i class="fas fa-file-pdf"></i> Exportar PDF</button>`.
- [ ] **Passo 3.4:** Crie uma `div` com o id `report-content`. **Todo o conteúdo do relatório (cards, gráficos e tabelas) deve ficar DENTRO desta div**.
- [ ] **Passo 3.5:** Desenvolva a estrutura visual dentro de `#report-content`:
  - Formulário de filtros.
  - Cards de resumo numérico (Valor Total, Qtd Itens).
  - Um elemento `<canvas id="topSellingChart"></canvas>` (para o gráfico de barras dos mais vendidos).
  - Tabelas de dados detalhados.
- [ ] **Passo 3.6:** Escreva o Javascript interno para instanciar o `Chart.js`, capturando as variáveis JSON passadas pela View via filtro `|safe` (ex: `const labels = {{ chart_labels_json|safe }};`).
- [ ] **Passo 3.7:** Escreva a função Javascript acoplada ao botão `btn-export-pdf`. Utilize o `html2pdf().set({ margin: 1, filename: 'relatorio_estoque.pdf', image: { type: 'jpeg', quality: 0.98 }, html2canvas: { scale: 2 }, jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' } }).from(document.getElementById('report-content')).save();`.

---

## Fase 4: Integração de Navegação
**Objetivo:** Adicionar o link do relatório ao menu.

- [ ] **Passo 4.1:** Abra `base/templates/base/sidebar.html`.
- [ ] **Passo 4.2:** Altere o href correspondente aos Relatórios de Estoque para `href="{% url 'stock:report-stock' %}"`.

---

## Fase 5: Validação Básica
**Objetivo:** Garantir a funcionalidade.

- [ ] **Passo 5.1:** Execute `python manage.py check`.
- [ ] **Passo 5.2:** Em `stock/tests.py`, crie um teste para verificar se `stock:report-stock` retorna *status code* 200 e se o contexto contém as chaves JSON dos gráficos.