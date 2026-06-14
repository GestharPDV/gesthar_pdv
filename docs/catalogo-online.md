# Plano de Ação Otimizado para Claude Code: Catálogo Online Público

**Contexto para o Agente:**
Você está trabalhando no projeto `gesthar_pdv` (Django, PostgreSQL, Bootstrap 5). Sua tarefa é implementar o Módulo de Catálogo Online Público que funciona como uma vitrine digital para clientes finais visualizarem, pesquisarem e adquirirem produtos em estoque, finalizando pedidos via WhatsApp da loja.

O catálogo é totalmente **público** (sem autenticação), deve reutilizar a identidade visual do `custom.css`, exibir apenas produtos com estoque disponível, e permitir um fluxo intuitivo de compra orientado ao WhatsApp.

---

## Fase 1: Ampliação de Modelos e Configurações
**Objetivo:** Estruturar a camada de dados para suportar múltiplas imagens de produtos e configurações do catálogo.

- [ ] **Passo 1.1:** Inspecione o modelo `Product` existente em `product/models.py`. Identifique os campos presentes (nome, preço, descrição, estoque, tipo, cor, tamanho, etc.).
- [ ] **Passo 1.2:** Amplie o modelo `Product` adicionando um campo `cover_image` (ImageField, opcional) para armazenar a capa/primeira imagem.
- [ ] **Passo 1.3:** Crie um novo modelo `ProductImage` em `product/models.py` com campos:
  - `product` (ForeignKey → Product, on_delete=CASCADE)
  - `image` (ImageField)
  - `order` (PositiveIntegerField, para ordenação: 1, 2, 3)
  - `created_at` (DateTimeField, auto_now_add=True)
  - Com restrição: máximo 3 imagens por produto
- [ ] **Passo 1.4:** Crie um novo app `catalog` (`python manage.py startapp catalog`). Registre-o em `INSTALLED_APPS` no `settings.py`.
- [ ] **Passo 1.5:** Crie um modelo `CatalogConfig` em `catalog/models.py` com campos:
  - `whatsapp_number` (CharField, max_length=20, formato: 5511999999999)
  - `catalog_visible` (BooleanField, default=True)
  - `company_name` (CharField, max_length=255)
  - `created_at` (DateTimeField, auto_now_add=True)
  - `updated_at` (DateTimeField, auto_now=True)
- [ ] **Passo 1.6:** Execute `python manage.py makemigrations` e `python manage.py migrate` para criar as tabelas.
- [ ] **Passo 1.7:** Registre ambos os modelos em `product/admin.py` e `catalog/admin.py` para gerenciamento via Admin Django.

---

## Fase 2: Views e URLs (Backend)
**Objetivo:** Criar endpoints públicos para listagem, busca, filtros e redirecionamento para WhatsApp.

- [ ] **Passo 2.1:** Em `catalog/views.py`, importe os modelos necessários (Product, ProductImage, CatalogConfig) e use `from django.views.generic import TemplateView, View`.
- [ ] **Passo 2.2:** Crie a view `CatalogListView(TemplateView)`:
  - Template: `catalog/catalog_list.html`
  - No `get_context_data`: recupere todos os produtos com `stock > 0`
  - Passe lista de produtos, filtros disponíveis (tipos, cores, tamanhos) e configurações do catálogo
  - Não requer autenticação (`LoginRequiredMixin` NOT used)
- [ ] **Passo 2.3:** Crie a view `ProductDetailView(View)` que retorna JSON (AJAX):
  - Receba `product_id` via GET
  - Retorne dados: nome, preço, descrição, estoque, imagens (até 3), variações
  - Use `from django.http import JsonResponse`
  - Valide estoque antes de retornar (exiba apenas se > 0)
- [ ] **Passo 2.4:** Crie a view `SearchProductsView(View)` que retorna JSON (AJAX):
  - Receba parâmetro `q` (query) via GET
  - Busque por: ID, nome, tipo de roupa, cor, qualquer outro campo relevante
  - Implemente com `Q` queries do Django ORM (case-insensitive)
  - Implemente debounce no frontend (300ms)
  - Retorne lista de produtos encontrados
- [ ] **Passo 2.5:** Crie a view `FilterProductsView(View)` que retorna JSON (AJAX):
  - Receba parâmetros via GET: `type`, `color`, `size`, `price_min`, `price_max`, `sort_by`
  - Filtre produtos cumulativamente
  - Suporte ordenação: `relevance` (padrão), `name_asc`, `price_asc`, `price_desc`, `newest`
  - Validar estoque (apenas > 0)
- [ ] **Passo 2.6:** Crie a view `WhatsAppRedirectView(View)`:
  - Receba dados do carrinho via POST (JSON): lista de itens com produto_id, variações, quantidade
  - Valide estoque de cada item no backend (segurança)
  - Gere mensagem formatada com lista de produtos, quantidades, variações e total
  - Codifique corretamente a URL usando `urllib.parse.quote()`
  - Redirecione para: `https://wa.me/{NUMERO}?text={MENSAGEM}`
  - Se houver erro (estoque indisponível), retorne erro JSON
- [ ] **Passo 2.7:** Em `catalog/urls.py`, registre as URLs:
  - `path('', views.CatalogListView.as_view(), name='catalog-list')`
  - `path('api/product/<int:product_id>/', views.ProductDetailView.as_view(), name='product-detail')`
  - `path('api/search/', views.SearchProductsView.as_view(), name='search-products')`
  - `path('api/filter/', views.FilterProductsView.as_view(), name='filter-products')`
  - `path('api/whatsapp-redirect/', views.WhatsAppRedirectView.as_view(), name='whatsapp-redirect')`
- [ ] **Passo 2.8:** Em `core/urls.py`, inclua as URLs do catalog: `path('catalog/', include('catalog.urls'))`

---

## Fase 3: Templates (Frontend - Estrutura HTML)
**Objetivo:** Renderizar a página pública do catálogo com layout responsivo, respeitando o design do `custom.css`.

- [ ] **Passo 3.1:** Crie `catalog/templates/catalog/catalog_list.html` estendendo `base/base.html`.
- [ ] **Passo 3.2:** No `{% block content %}`, construa a estrutura:
  - **Header:** Logo da empresa + Logo Gesthar + barra de busca + ícone do carrinho (com badge de contador)
  - **Layout:** Grid de 2 colunas (desktop) / 1 coluna (mobile)
    - Coluna esquerda (mobile em cima): Painel de filtros (drawer em mobile)
    - Coluna direita: Grid de produtos responsivo (4 colunas desktop, 2 tablet, 1 mobile)
- [ ] **Passo 3.3:** Crie o **painel de filtros** com:
  - Input de busca com ícone de lupa
  - Select de Tipo de Roupa (carregado via backend)
  - Checkboxes de Tamanho
  - Checkboxes de Cor
  - Range Slider de Faixa de Preço
  - Toggle de Disponibilidade em Estoque
  - Select de Ordenação (Relevância, Nome, Preço baixo-alto, Preço alto-baixo)
  - Botão "Limpar Filtros"
- [ ] **Passo 3.4:** Crie o **grid de cards de produtos**:
  - Cada card exibe: imagem (cover), nome, preço, indicador de variações (badge), ação de visualização
  - Cards são clicáveis e abrem modal (não navigation)
  - Respeitam espaçamentos e tipografia do `custom.css`
- [ ] **Passo 3.5:** Crie o **modal de detalhes do produto** (inicialmente oculto):
  - Galeria de imagens (até 3) com navegação (setas ou thumbnails)
  - Título, preço, descrição
  - Seção de variações (selects/checkboxes para tamanho, cor, etc.)
  - Input spinner de quantidade (mín 1, máx = estoque disponível)
  - Botão "Adicionar ao Carrinho"
  - Botão X para fechar ou clique fora
- [ ] **Passo 3.6:** Crie um **footer** com informações de contato, copyright e links úteis.

---

## Fase 4: JavaScript (Interatividade - LocalStorage, AJAX, Modal)
**Objetivo:** Implementar lógica de cliente: gerenciamento de carrinho, busca, filtros, modal e integração com WhatsApp.

- [ ] **Passo 4.1:** Crie `catalog/static/catalog/js/catalog.js` (arquivo principal):
  - Implemente **Carrinho em LocalStorage**:
    - Função `getCart()`: recupera carrinho do localStorage ou retorna array vazio
    - Função `saveCart(cartItems)`: persiste carrinho no localStorage com timestamp
    - Função `addToCart(productId, variations, quantity)`: adiciona item validando quantidade
    - Função `removeFromCart(productId, variations)`: remove item específico
    - Função `updateCartBadge()`: atualiza contador no header
    - Função `clearCart()`: limpa ao finalizar pedido
- [ ] **Passo 4.2:** Implemente **Modal Management**:
  - Função `openProductModal(productId)`: faz AJAX para obter dados completos do produto
  - Função `closeProductModal()`: fecha modal (X, ESC, clique fora)
  - Função `updateGallery(images)`: renderiza galeria de imagens
- [ ] **Passo 4.3:** Implemente **AJAX para Busca**:
  - Event listener no input de busca com debounce de 300ms
  - AJAX GET para `/catalog/api/search/?q={query}`
  - Atualiza grid de produtos com resultados
  - Mensagem "Nenhum produto encontrado" se resultado vazio
- [ ] **Passo 4.4:** Implemente **AJAX para Filtros**:
  - Event listeners em cada filtro (select, checkbox, range slider)
  - Quando filtro muda, fazer AJAX GET para `/catalog/api/filter/?type=...&color=...&sort_by=...`
  - Atualizar grid de produtos
  - Manter URL atualizada (opcional, para compatibilidade com share)
- [ ] **Passo 4.5:** Implemente **Galeria de Imagens**:
  - Navegação por setas (próxima/anterior)
  - Thumbnails clicáveis
  - Indicador de imagem atual (ex: "1/3")
- [ ] **Passo 4.6:** Implemente **Carrinho (Visualização/Edição)**:
  - Função `showCartDrawer()`: exibe drawer lateral com itens do carrinho
  - Cada item mostra: imagem, nome, variações, quantidade, preço unitário, subtotal, botão remover
  - Spinner para editar quantidade (com limite de estoque)
  - Total geral recalculado em tempo real
  - Botão "Finalizar Pedido"
- [ ] **Passo 4.7:** Implemente **Integração com WhatsApp**:
  - Função `finalizeOrder()`: coleta carrinho, valida estoque, monta mensagem
  - AJAX POST para `/catalog/api/whatsapp-redirect/` com dados do carrinho
  - Tratamento de erro (estoque indisponível)
  - Redireciona para WhatsApp ou exibe erro em toast
  - Formato da mensagem:
    ```
    Olá! Gostaria de fazer um pedido:

    PRODUTO 1
    - Descrição: [Nome do Produto]
    - Variações: Tamanho M, Cor Rosa
    - Quantidade: 2
    - Subtotal: R$ XX,XX

    TOTAL: R$ XXX,XX
    ```

---

## Fase 5: Estilos CSS (Integração com custom.css)
**Objetivo:** Garantir que o catálogo se integre visualmente ao sistema existente, reutilizando paleta, tipografia e espaçamentos.

- [ ] **Passo 5.1:** Crie `catalog/static/catalog/css/catalog.css` (estilos específicos do catálogo).
- [ ] **Passo 5.2:** Analise o `static/css/custom.css` para identificar:
  - Paleta de cores (primária, secundária, neutras, alertas)
  - Tipografia (font-family, sizes, weights)
  - Espaçamentos (padding, margin, gap)
  - Estilos de botões, inputs, cards, modals
- [ ] **Passo 5.3:** Implemente estilos para:
  - Header: layout flexível, responsivo, logo + barra de busca + ícone carrinho
  - Layout 2-colunas (sidebar filtros + grid produtos) com media queries
  - Cards de produtos: hover effect sutil, transições, badges
  - Painel de filtros: styled select/checkboxes/range slider
  - Modal: overlay, 90% viewport, responsivo
  - Drawer do carrinho: side panel animado
  - Mensagens de erro/sucesso: toast notifications
- [ ] **Passo 5.4:** Valide responsividade:
  - Desktop (1024px+): 4 colunas produtos
  - Tablet (768px-1023px): 2 colunas produtos, filtros em drawer
  - Mobile (< 768px): 1 coluna produtos, filtros em drawer
  - Touch-friendly: áreas clicáveis mín 44x44px
- [ ] **Passo 5.5:** Garanta consistência com `custom.css`:
  - Paleta de cores sem conflitos
  - Tipografia alinhada
  - Espaçamentos harmônicos
  - Sem elementos administrativos visíveis

---

## Fase 6: Validação, Testes e Segurança
**Objetivo:** Garantir que o catálogo é funcional, seguro e responsivo.

- [ ] **Passo 6.1:** Em `catalog/tests.py`, crie testes unitários para views:
  - `TestCatalogListView`: GET retorna 200, contexto contém produtos com estoque > 0
  - `TestProductDetailView`: AJAX retorna JSON correto com imagens, preço, variações
  - `TestSearchProductsView`: busca por nome/tipo/cor retorna resultados corretos, debounce funciona
  - `TestFilterProductsView`: filtros individuais e cumulativos funcionam, ordenação correta
  - `TestWhatsAppRedirectView`: validação de estoque, mensagem formatada, redirecionamento correto
- [ ] **Passo 6.2:** Valide segurança:
  - Inputs são sanitizados (busca, filtros) contra SQL injection e XSS
  - CSRF protection em POST (WhatsApp redirect)
  - Rate limiting opcional em endpoints de busca (considerar)
  - Informações administrativas não são expostas (nenhum campo sensível em JSON)
- [ ] **Passo 6.3:** Valide responsividade manual:
  - Desktop (Chrome, Firefox)
  - Tablet (Chrome DevTools simulado)
  - Mobile (Chrome DevTools simulado + dispositivo real se disponível iOS/Android)
- [ ] **Passo 6.4:** Teste fluxos completos:
  - Acesso catálogo público (sem login) ✓
  - Busca por produto ✓
  - Aplicação de filtros ✓
  - Abertura de modal com galeria ✓
  - Adição de item ao carrinho (persistência localStorage) ✓
  - Edição de quantidade/variações no carrinho ✓
  - Remoção de item ✓
  - Finalização via WhatsApp com mensagem pré-formatada ✓
- [ ] **Passo 6.5:** Execute `python manage.py test catalog` e corrija falhas.

---

## Fase 7: Integração e Deploy
**Objetivo:** Integrar catálogo ao sistema e preparar para produção.

- [ ] **Passo 7.1:** Configure o número WhatsApp da loja via Admin Django (modelo `CatalogConfig`).
- [ ] **Passo 7.2:** Adicione link para o catálogo em local acessível publicamente (ex: footer do site, se houver landing page).
- [ ] **Passo 7.3:** Configure `robots.txt` se catálogo deve ser indexável em buscadores.
- [ ] **Passo 7.4:** Adicione meta tags (title, description, og:image) na página do catálogo para SEO básico.
- [ ] **Passo 7.5:** Teste em ambiente de staging com dados reais.
- [ ] **Passo 7.6:** Valide permissões de acesso: catálogo deve ser 100% público (nenhuma restrição de autenticação).
- [ ] **Passo 7.7:** Deploy para produção.

---

## Considerações de Engenharia

1. **Estrutura de Imagens:** Use modelo `ProductImage` separado para máxima flexibilidade. Se performance for crítica, considere cache em CloudFront ou S3.

2. **Busca em Tempo Real:** O debounce de 300ms é suficiente para evitar sobrecarga. Se precisar de busca muito rápida, considere Elasticsearch no futuro.

3. **Validação de Estoque:** Sempre valide no backend antes de gerar URL WhatsApp, pois estoque pode mudar entre requisições. Não confie apenas em LocalStorage.

4. **LocalStorage:** Inclua timestamp para limpeza automática de carrinhos antigos (opcional, ex: > 24 horas). Verificar ao carregar página.

5. **URL WhatsApp:** Usar `urllib.parse.quote()` em Python para RFC 3986 compliance. Testar em browser reais (especialmente mobile).

6. **Performance:** Carregamento inicial target < 2s em 4G. Busca AJAX target < 500ms. Usar Django's QuerySet optimization (select_related, prefetch_related).

7. **Responsividade:** Testar em dispositivos reais. Bootstrap 5 oferece containers e breakpoints já prontos em `custom.css`.

8. **Edge Cases:**
   - Carrinho vazio: desabilitar botão "Finalizar Pedido"
   - Produto removido do catálogo durante sessão: notificar ao finalizar
   - Múltiplas variações não selecionadas: validar antes de adicionar
   - Quantidade solicitada > estoque: limitar spinner ao máximo disponível

9. **Código Organizado:**
   - Views em `catalog/views.py` (sem lógica complexa, delegue a services)
   - Opcionalmente: criar `catalog/services.py` para lógica de negócio
   - Templates estruturados em `catalog/templates/catalog/`
   - CSS modular em `catalog/static/catalog/css/`
   - JavaScript modular (considerar dividir em múltiplos arquivos se crescer)

---

**Documento versão:** 1.0  
**Data:** Abril 2026  
**Status:** Pronto para Implementação  
**Módulo:** Catálogo Online Público (`catalog`)
