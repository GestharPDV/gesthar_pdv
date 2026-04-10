# Plano de Ação Otimizado para Claude Code: Relatórios de Estoque (RF016)

**Contexto para o Agente:**
Você está trabalhando no projeto `gesthar_pdv` (Django, PostgreSQL, Bootstrap 5). Sua tarefa é implementar o Módulo de Relatórios de Estoque (RF016) com recursos visuais e exportação para PDF, seguindo estritamente a interface visual do Protótipo B.13 e a modelagem do banco de dados (tabelas `PRODUTO`, `PRODUTO_COR_TAMANHO` e `MOVIMENTO_ESTOQUE`).

---

## Fase 1: Camada de Serviços (Consultas ORM)
**Objetivo:** Criar funções precisas para extrair os indicadores de estoque, respeitando a granularidade das variações.

- [ ] **Passo 1.1:** Abra `stock/services.py` (crie se não existir). Importe os modelos necessários (`Produto`, `ProdutoCorTamanho`, `MovimentoEstoque`, etc.).
- [ ] **Passo 1.2:** Crie `get_total_pieces()`: Calcule a quantidade física total de peças somando o campo de quantidade da tabela de variações (`PRODUTO_COR_TAMANHO`).
- [ ] **Passo 1.3:** Crie `get_inventory_valuation()`: Calcule o valor total do estoque multiplicando a quantidade atual pelo preço de venda unitário.
- [ ] **Passo 1.4:** Crie `get_low_stock_variations()`: Filtre as variações específicas (`PRODUTO_COR_TAMANHO`) onde a quantidade atual é menor ou igual ao `estoque_minimo` definido no produto pai.
- [ ] **Passo 1.5:** Crie `get_inventory_movements(start_date, end_date)`: Retorne o histórico de entradas e saídas no período consultando a tabela `MOVIMENTO_ESTOQUE`.
- [ ] **Passo 1.6:** Crie `get_quantity_by_category()`: Agrupe o estoque atual por Categoria para alimentar o gráfico de pizza.
- [ ] **Passo 1.7:** Crie `get_quantity_by_color()`: Agrupe o estoque atual por Cor (usando a tabela de variações) para alimentar o gráfico de barras.

---

## Fase 2: Controladores e Estrutura de Dados (Views e URLs)
**Objetivo:** Criar a view e preparar os dados no formato correto (JSON) para os gráficos aprovados.

- [ ] **Passo 2.1:** Em `stock/views.py`, crie a classe `StockReportView` herdando de `LoginRequiredMixin` e `TemplateView` (template: `stock/report_stock.html`).
- [ ] **Passo 2.2:** No método `get_context_data`, processe os filtros (Data Inicial, Data Final, Categoria) a partir de `self.request.GET`.
- [ ] **Passo 2.3:** Formate os dados de "Quantidade por Categoria" e "Quantidade por Cor" em dicionários e converta-os para strings JSON usando `json.dumps()`. Injete essas strings no contexto (ex: `context['category_chart_json']`, `context['color_chart_json']`).
- [ ] **Passo 2.4:** Injete no contexto o valor de `total_pieces` e `inventory_valuation`.
- [ ] **Passo 2.5:** Em `stock/urls.py`, registre a rota `path('relatorios/estoque/', views.StockReportView.as_view(), name='report-stock')`.

---

## Fase 3: Interface de Usuário, Gráficos e Exportação PDF (Templates)
**Objetivo:** Construir o Dashboard responsivo, renderizar os gráficos corretos e implementar o motor de exportação PDF de forma segura.

- [ ] **Passo 3.1:** Crie `stock/templates/stock/report_stock.html` estendendo `base/base.html`.
- [ ] **Passo 3.2:** No bloco de scripts (`{% block scripts %}`), adicione as CDNs do Chart.js e do html2pdf:
  - `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`
  - `<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>`
- [ ] **Passo 3.3:** Crie o botão de exportação no topo da página: `<button id="btn-export-pdf" class="btn btn-danger"><i class="fas fa-file-pdf"></i> Exportar PDF</button>`.
- [ ] **Passo 3.4:** Crie uma `div` com o id `report-content`. **Todo o conteúdo do relatório deve ficar DENTRO desta div**.
- [ ] **Passo 3.5:** Desenvolva a estrutura visual dentro de `#report-content`:
  - Formulário de filtros.
  - Cards de resumo numérico (Total de Peças, Valor Total do Estoque).
  - Dois elementos `<canvas>`: `<canvas id="categoryChart"></canvas>` (Gráfico de Pizza/Doughnut) e `<canvas id="colorChart"></canvas>` (Gráfico de Barras).
  - Tabelas de dados detalhados (Movimentações do período e Produtos com estoque baixo, exibindo as colunas de Tamanho e Cor).
- [ ] **Passo 3.6:** Escreva o Javascript interno para instanciar o `Chart.js`, capturando as variáveis JSON passadas pela View via filtro `|safe`. **ATENÇÃO:** Nas opções de configuração de ambos os gráficos, adicione `animation: false` para garantir que a renderização seja instantânea e não quebre a exportação.
- [ ] **Passo 3.7:** Escreva a função Javascript acoplada ao botão `btn-export-pdf`. Utilize o `html2pdf().set({ margin: 1, filename: 'relatorio_estoque.pdf', image: { type: 'jpeg', quality: 0.98 }, html2canvas: { scale: 2 }, jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' } }).from(document.getElementById('report-content')).save();`.

---

## Fase 4: Integração de Navegação
**Objetivo:** Adicionar o link do relatório ao menu lateral.

- [ ] **Passo 4.1:** Abra `base/templates/base/sidebar.html`.
- [ ] **Passo 4.2:** Altere o href correspondente aos Relatórios de Estoque para `href="{% url 'stock:report-stock' %}"`.

---

## Fase 5: Validação Básica
**Objetivo:** Garantir a funcionalidade.

- [ ] **Passo 5.1:** Execute `python manage.py check`.
- [ ] **Passo 5.2:** Em `stock/tests.py`, crie um teste simples para verificar se a rota `stock:report-stock` retorna status code 200 e se o contexto contém as chaves JSON dos gráficos e o total de peças.