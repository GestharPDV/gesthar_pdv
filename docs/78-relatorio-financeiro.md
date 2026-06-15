# Plano de Ação Otimizado para Claude Code: Dashboard Financeiro (Relatório de Vendas)

**Contexto para o Agente:**
Você está trabalhando no projeto `gesthar_pdv` (Django, PostgreSQL, Bootstrap 5).
Sua tarefa é implementar o Relatório Financeiro/Vendas na forma de um Dashboard gerencial. O sistema deve calcular indicadores de rentabilidade (CMV, Lucro, Ticket Médio), faturamento e curva ABC utilizando o ORM do Django. Os dados serão renderizados de forma nativa no frontend utilizando Chart.js com base em objetos JSON gerados pelas Views. O acesso deve ser restrito a administradores.

---

## Fase 1: Preparação de Dados e Regras de Negócio (`services.py`)

**Objetivo:** Isolar a lógica matemática e as consultas pesadas de banco de dados na camada de serviços.

* [ ] **Passo 1.1:** Em `sales/services.py`, crie as funções de rentabilidade:
* `get_financial_indicators(start_date, end_date)`: Agrega Receita Bruta (`gross_amount`), Total de Descontos (`discount_amount`), CMV (soma do custo base * quantidade em `SaleItem`) e Margem de Lucro Líquida. Considere apenas vendas com status `COMPLETED`.
* `get_average_ticket(start_date, end_date)`: Calcula o Ticket Médio (Receita Líquida / Vendas Concluídas).


* [ ] **Passo 1.2:** Crie a função de inteligência de estoque:
* `get_abc_curve(start_date, end_date)`: Agrupa `SaleItem` por produto/variação, ordenando por Faturamento Gerado no período para identificar os itens mais rentáveis.



---

## Fase 2: Construção da View Gerencial (Controller)

**Objetivo:** Capturar filtros do usuário, processar os dados via services e empacotar tudo em JSON e contexto para a renderização visual.

* [ ] **Passo 2.1:** Em `sales/views.py`, crie a classe `FinancialDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView)`.
* [ ] **Passo 2.2:** Defina `template_name = 'sales/financial_dashboard.html'`.
* [ ] **Passo 2.3:** Sobrescreva o método `get_context_data(self, kwargs)` para capturar variáveis via `self.request.GET` (como `start_date`, `end_date`).
* [ ] **Passo 2.4:** Chame as funções criadas no Passo 1.1 e 1.2. Armazene os valores escalares resultantes no contexto.
* [ ] **Passo 2.5:** Serialize os dados temporais e categóricos para os gráficos utilizando `json.dumps()` e envie para o contexto (ex: `payment_methods_json` reaproveitando as funções já existentes e `sales_evolution_json`).

---

## Fase 3: Criação da Interface Base (Templates - UI/Cards)

**Objetivo:** Construir a estrutura HTML da página utilizando Bootstrap 5, o formulário de filtros, Cards totalizadores e instanciar os gráficos.

* [ ] **Passo 3.1:** Crie o arquivo `sales/templates/sales/financial_dashboard.html`.
* [ ] **Passo 3.2:** No topo do layout, adicione um `<form method="GET">` inline com campos de data para Início e Fim, e um botão "Filtrar".
* [ ] **Passo 3.3:** Crie um sistema de grid para exibir Cards em destaque: Receita Bruta, Receita Líquida, CMV, Margem de Lucro, Ticket Médio e Descontos Aplicados.
* [ ] **Passo 3.4:** Adicione a importação da biblioteca Chart.js via CDN no final do documento.
* [ ] **Passo 3.5:** Crie as tags `<canvas>` e utilize scripts JS para instanciar um Gráfico de Rosca (Doughnut) para os meios de pagamento e um Gráfico de Linhas (Line) para a evolução diária de vendas.
* [ ] **Passo 3.6:** Crie uma Tabela HTML tradicional logo abaixo dos gráficos para exibir a Curva ABC (Nome do Produto, Qtd Vendida, Faturamento, Margem de Lucro).

---

## Fase 4: Roteamento e Permissões de Acesso

**Objetivo:** Tornar o Dashboard acessível pela barra de navegação sem expor dados sensíveis a usuários comuns.

* [ ] **Passo 4.1:** Em `sales/urls.py`, adicione a rota `path('relatorios/financeiro/', views.FinancialDashboardView.as_view(), name='financial-dashboard')`.
* [ ] **Passo 4.2:** Em `base/templates/base/sidebar.html`, insira o link apontando para `financial-dashboard`. Envolva o link em um bloco condicional de permissão (`{% if request.user.role == 'ADMIN' or request.user.is_superuser %}`). Não adicione ícones a este novo item, apenas o texto padrão do menu.

# Plano de Ação Otimizado: KPIs Avançados (ROI, Tempo de Estoque e Inteligência Preditiva)

**Contexto para o Agente:**
Implementação de métricas avançadas de BI no painel gerencial do `gesthar_pdv` utilizando Django. O foco é adicionar indicadores de alto valor estratégico: ROI de Estoque (GMROI), Tempo de Estoque (Giro e Cobertura) e Previsão de Ruptura, criando um diferencial competitivo para o sistema.

---

## Fase 1: Estrutura de Dados Base (Modelos)

**Objetivo:** Garantir que o banco de dados possui os campos fundamentais para cálculos de rentabilidade real.

* [ ] **Passo 1.1:** No arquivo `product/models.py`, verifique o modelo `Product` ou `ProductVariation`.
* [ ] **Passo 1.2:** Se não existir, adicione o campo `cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Preço de Custo")`. O custo é obrigatório para calcular o ROI (GMROI).
* [ ] **Passo 1.3:** Gere e aplique as migrações (`python manage.py makemigrations product` e `python manage.py migrate`).
* [ ] **Passo 1.4:** No arquivo `sales/models.py`, atualize o `SaleItem` para registrar o `unit_cost` no momento da venda (snapshot do custo), garantindo que mudanças futuras no preço de custo não alterem o histórico de lucro de vendas passadas.

---

## Fase 2: Motor de Cálculos (`services.py`)

**Objetivo:** Implementar as fórmulas matemáticas complexas isoladas da View.

* [ ] **Passo 2.1:** Em `stock/services.py` ou `sales/services.py`, crie a função `get_gmroi(start_date, end_date)`:
* **Fórmula:** (Margem Bruta / Custo Médio do Estoque).
* **Lógica:** Calcule a Margem Bruta (Receita Líquida - Custo dos Produtos Vendidos via `SaleItem.unit_cost`). Divida pelo valor total investido no estoque atual ativo.


* [ ] **Passo 2.2:** Crie a função `get_stock_coverage_and_turnover(product_id, days_analyzed=30)`:
* **Tempo de Estoque (Giro):** Calcule a média de itens vendidos por dia (`Sum(quantity)` / `days_analyzed`).
* **Cobertura de Estoque:** (Quantidade atual em estoque / Média de vendas diárias). Retorna quantos dias o estoque atual vai durar.


* [ ] **Passo 2.3:** Crie a função `get_stockout_risk_list()`:
* Identifique produtos da Curva A (alto faturamento) cuja "Cobertura de Estoque" seja inferior a 7 dias. Retorne uma lista de alertas.



---

## Fase 3: Integração com a View Gerencial

**Objetivo:** Injetar os novos indicadores no contexto do Dashboard.

* [ ] **Passo 3.1:** Em `sales/views.py`, na classe `FinancialDashboardView`, importe as novas funções criadas.
* [ ] **Passo 3.2:** No método `get_context_data`, adicione as chamadas:
* `context['gmroi_percentage'] = get_gmroi(...)`
* `context['stockout_alerts'] = get_stockout_risk_list()`


* [ ] **Passo 3.3:** Processe uma lista dos "Top 10 Produtos" contendo o Tempo de Estoque (Giro de dias) de cada um para compor uma tabela analítica.

---

## Fase 4: Interface e Visualização Diferenciada (UI)

**Objetivo:** Exibir os dados de forma clara e acionável para o gestor.

* [ ] **Passo 4.1:** Em `sales/templates/sales/financial_dashboard.html`, adicione dois novos Cards em destaque na parte superior:
* **ROI de Estoque (GMROI):** Exiba o percentual. Adicione um tooltip (Bootstrap) explicando: *"Retorno gerado para cada R$ 1,00 investido em mercadoria."*
* **Capital Imobilizado:** O valor financeiro total parado no estoque no momento atual.


* [ ] **Passo 4.2:** Crie uma seção de **"Radar de Ruptura (Alerta Crítico)"**:
* Renderize a lista `stockout_alerts`.
* Formate com cores de atenção (amarelo/vermelho). Exiba: *Produto X - Restam Y unidades (Cobertura: Z dias).*


* [ ] **Passo 4.3:** Na Tabela de Produtos (Curva ABC), adicione a coluna **Dias de Estoque (Giro)**. Produtos com alto giro (vende rápido) devem receber um ícone verde; produtos encalhados (mais de 90 dias de cobertura) devem receber um ícone de alerta vermelho.

---

## Fase 5: Segurança e Otimização de Queries

**Objetivo:** Prevenir lentidão no carregamento do painel.

* [ ] **Passo 5.1:** Ao calcular o Custo Total do Estoque, faça a agregação diretamente no banco: `ProductVariation.objects.aggregate(total=Sum(F('stock') * F('product__cost_price')))` utilizando a função `ExpressionWrapper`.
* [ ] **Passo 5.2:** Utilize cache (`django.core.cache`) nas funções de análise preditiva (como o Radar de Ruptura), com expiração de 1 hora, para evitar sobrecarga no banco de dados a cada F5 (refresh) que o gestor der no dashboard.