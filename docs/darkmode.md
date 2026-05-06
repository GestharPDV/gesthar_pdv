# Implementação de Dark Mode — Gesthar PDV

**Objetivo:** Adicionar funcionalidade de Modo Escuro (Dark Mode) ao sistema Gesthar, aproveitando as variáveis CSS existentes (`custom.css`) e o suporte nativo do Bootstrap 5.3, com persistência da preferência do usuário via `localStorage`.

---

## Fase 1: Variáveis CSS Globais
**Objetivo:** Criar a paleta de cores para o modo escuro sobrescrevendo as variáveis existentes quando o tema escuro estiver ativo.

**Arquivo:** `static/css/custom.css`

- [x] **Passo 1.1:** Logo após o bloco `:root { }`, adicione o seletor `[data-bs-theme="dark"]` com as variáveis de cor e os ajustes específicos de componentes:

```css
[data-bs-theme="dark"] {
  --cor-botao-secundario-rosa: #2d2225;
  --cor-fonte-preta: #e4e4e4;
  --cor-fonte-cinza: #888888;
  --cor-fundo-site: #121212;
  --cor-fundo-cabecalho: #1e1e1e;
  --cor-fundo-linha: #2c2c2c;
  --cor-fundo-rodape: #1e1e1e;
  --cor-fundo-categoria: #1e1e1e;
  --cor-cabecalho-formulario: #1e1e1e;
}

[data-bs-theme="dark"] .pdv-box-unificado {
    background-color: var(--cor-fundo-site);
    border-color: #333 !important;
}

[data-bs-theme="dark"] .pdv-footer-interno {
    background-color: var(--cor-fundo-cabecalho);
    border-color: #333 !important;
}

[data-bs-theme="dark"] .table {
    --bs-table-bg: transparent;
    --bs-table-color: var(--cor-fonte-preta);
}
```

---

## Fase 2: Lógica de Alternância e Persistência (JavaScript)
**Objetivo:** Criar o script que aplica o tema salvo e a função de alternar (toggle).

**Arquivo:** `base/templates/base/base.html`

- [x] **Passo 2.1:** Para evitar o "Flash of Unstyled Content" (FOUC), adicione o seguinte script dentro da tag `<head>`, logo abaixo do bloco `<style>`:

```html
<script>
    const storedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', storedTheme);
</script>
```

- [x] **Passo 2.2:** Antes do fechamento de `</body>` (antes do `{% block scripts_extra %}`), adicione a função de alternância:

```html
<script>
    function toggleDarkMode() {
        const htmlEl = document.documentElement;
        const newTheme = htmlEl.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
        htmlEl.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    }
</script>
```

---

## Fase 3: Botão Toggle na Sidebar
**Objetivo:** Adicionar o botão para o usuário ativar/desativar o Dark Mode, no mesmo padrão visual do botão de Alertas.

**Arquivo:** `base/templates/base/sidebar.html`

- [x] **Passo 3.1:** Adicione o botão imediatamente após o bloco `</a>` do link de Alertas, antes da `div.footer-logo`. Use o mesmo padrão de classes do link de Alertas:

```html
<button onclick="toggleDarkMode()"
        class="btn d-flex align-items-center justify-content-between p-2 mb-2 rounded link-sidebar w-100 border-0 position-relative"
        style="background: transparent;">
  <div class="d-flex align-items-center">
    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="none"
         viewBox="0 0 24 24" stroke="currentColor" class="icon-sidebar flex-shrink-0">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M21.752 15.002A9.72 9.72 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z" />
    </svg>
    <span class="ms-3 text-label fw-semibold">MODO ESCURO</span>
  </div>
</button>
```

> O `text-label` garante que o texto some automaticamente quando a sidebar estiver recolhida.

---

## Fase 4: Correções por Página
**Objetivo:** Corrigir páginas que definem suas próprias variáveis CSS locais (`:root`) ou usam classes Bootstrap que não respondem ao dark mode.

### 4.1 — `sales/templates/sales/open_register.html` e `close_register.html`

**Problema:** Cada template define um bloco `:root` com cores fixas para o modo claro (`--bg-body`, `--bg-card`, `--text-main`, etc.) e o `.input-cash` tem `background-color: #f9f9f9 !important`.

- [x] **Passo 4.1.1:** Após o bloco `:root { }` em cada template, adicione:

```css
[data-bs-theme="dark"] {
    --bg-body: #121212;
    --bg-card: #1e1e1e;
    --text-main: #e4e4e4;
    --text-secondary: #aaaaaa;
    --border-color: #444444;
}

[data-bs-theme="dark"] .input-cash {
    background-color: #2c2c2c !important;
}
```

- [x] **Passo 4.1.2:** No `close_register.html`, inclua também `--highlight-bg` no bloco acima:

```css
[data-bs-theme="dark"] {
    /* ... variáveis anteriores ... */
    --highlight-bg: #2d1f24;
}
```

---

### 4.2 — `sales/templates/sales/pdv.html`

**Problemas encontrados:**
- `{% block main_class %}` usava `bg-light`, fixando o fundo no modo claro.
- Bloco `:root` local sem override dark mode.
- Elementos com `bg-white`, `bg-light` e `text-dark` hardcoded no HTML e em strings JavaScript geradas dinamicamente.

- [x] **Passo 4.2.1:** Remova `bg-light` do bloco `main_class`:

```html
{% block main_class %}p-0 overflow-hidden{% endblock %}
```

- [x] **Passo 4.2.2:** Após o bloco `:root { }` no `<style>` do template, adicione:

```css
[data-bs-theme="dark"] {
    --bg-body: #121212;
    --bg-card: #1e1e1e;
    --text-main: #e4e4e4;
    --text-secondary: #aaaaaa;
    --border-color: #444444;
}

[data-bs-theme="dark"] .table-hover-custom tbody tr:hover { background: #2c2c2c; }
[data-bs-theme="dark"] #search-results { background-color: var(--bg-card) !important; }
[data-bs-theme="dark"] #step-change .rounded-4 { background-color: #1e1e1e !important; }
[data-bs-theme="dark"] #step-success .rounded-4 { background-color: #1a3a1a !important; }
```

- [x] **Passo 4.2.3:** No HTML estático, remova `bg-white` do div de cliente vinculado:

```html
<!-- Antes -->
<div class="d-flex justify-content-between align-items-center bg-white rounded-pill ...">

<!-- Depois -->
<div class="d-flex justify-content-between align-items-center rounded-pill ...">
```

- [x] **Passo 4.2.4:** Na string JavaScript que renderiza os itens da busca, troque `text-dark` por `text-body` (adapta ao tema):

```js
// Antes
<div class="fw-semibold text-dark">${item.label}</div>

// Depois
<div class="fw-semibold text-body">${item.label}</div>
```

- [x] **Passo 4.2.5:** Na string JavaScript da caixa de pagamento, troque `bg-light` por inline style com variável controlada:

```js
// Antes
<div class="p-4 rounded bg-light border border-dashed">

// Depois
<div class="p-4 rounded border border-dashed" style="background-color: var(--bg-card);">
```

- [x] **Passo 4.2.6:** No HTML do rodapé da tabela, troque `text-dark` por `text-body` no subtotal:

```html
<!-- Antes -->
<div id="display-subtotal" class="fw-bold text-dark">

<!-- Depois -->
<div id="display-subtotal" class="fw-bold text-body">
```

---

### 4.3 — `product/forms.py`

**Problema:** Os widgets dos formulários recebiam a classe `TAILWIND_CLASSES`, que continha `bg-white`. Como o projeto usa Bootstrap (não Tailwind), essa classe era aplicada via Bootstrap como fundo branco `!important`, impedindo o dark mode.

- [x] **Passo 4.3.1:** Substitua a constante `TAILWIND_CLASSES` por uma função auxiliar que aplica `form-control` (inputs/textareas) ou `form-select` (selects) — classes do Bootstrap 5.3 que respondem corretamente ao dark mode:

```python
def _apply_bootstrap_classes(fields):
    for field in fields.values():
        widget = field.widget.__class__.__name__
        if widget == "CheckboxInput":
            continue
        if "Select" in widget:
            field.widget.attrs["class"] = "form-select"
        else:
            field.widget.attrs["class"] = "form-control"
```

- [x] **Passo 4.3.2:** Substitua o loop de estilização nos `__init__` de `ProductForm`, `ProductSupplierForm` e `ProductVariationForm` pela chamada à função:

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # ... querysets ...
    _apply_bootstrap_classes(self.fields)
```

---

## Fase 5: Validação
- [ ] **Passo 5.1:** Verifique se o clique no botão "MODO ESCURO" na sidebar alterna o atributo `data-bs-theme` na tag `<html>` entre `"dark"` e `"light"`.
- [ ] **Passo 5.2:** Atualize a página e verifique se a escolha do tema persiste (via `localStorage`).
- [ ] **Passo 5.3:** Teste as rotas `/sales/open-register/`, `/sales/close-register/`, `/sales/pdv/` e `/products/create/` no modo escuro e verifique fundos, inputs e textos.
- [ ] **Passo 5.4:** Verifique o dropdown de busca de produtos no PDV — o nome do produto deve ser legível sobre o fundo escuro.
- [ ] **Passo 5.5:** Verifique a caixa de pagamento no modal do PDV — deve ter fundo escuro no dark mode.
