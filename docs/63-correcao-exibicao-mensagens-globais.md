# Plano de Ação Otimizado: Correção de Exibição de Mensagens Globais (Issue #63)

**Contexto para o Agente:**
Você está trabalhando no projeto `gesthar_pdv` (Django, HTML, Bootstrap 5). Atualmente, a notificação de "Caixa fechado" disparada em `sales/views.py` (`close_register_view`) não é exibida após o redirecionamento para a Home Page (`base:home`). O problema ocorre porque o bloco de renderização do `django.contrib.messages` está injetado localmente em templates específicos (como `pdv.html`) em vez de estar no layout global da aplicação (`base.html`). A tarefa é centralizar o sistema de alertas no template base para que funcione em todo o sistema.

---

## Fase 1: Injeção Global do Sistema de Mensagens
**Objetivo:** Adicionar o bloco de mensagens do Django no template principal para que todas as páginas herdem essa funcionalidade.

- [ ] **Passo 1.1:** Abra o arquivo `base/templates/base/base.html`.
- [ ] **Passo 1.2:** Localize a tag `<main>` ou o interior imediato da div principal do layout (`<div class="d-flex h-100 w-100 overflow-hidden">`).
- [ ] **Passo 1.3:** Cole o seguinte bloco de código responsável por exibir as mensagens e aplicar o comportamento de *auto-dismiss* (desaparecer automaticamente) garantindo que fique em um nível superior de `z-index`:
```html
{% if messages %}
<div class="toast-container position-fixed top-0 start-50 translate-middle-x p-3 mt-3" style="z-index: 1055;">
    {% for message in messages %}
    <div class="alert alert-{{ message.tags }} alert-dismissible fade show shadow-sm auto-dismiss mb-2" role="alert">
        {{ message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
    {% endfor %}
</div>
<script>
  document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.auto-dismiss');
    alerts.forEach(function(alert) {
      setTimeout(function() {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      }, 4000);
    });
  });
</script>
{% endif %}
```

---

## Fase 2: Limpeza e Remoção de Duplicidades (DRY)
**Objetivo:** Remover os blocos de mensagens de templates locais que agora se tornaram redundantes, evitando comportamentos duplicados.

- [ ] **Passo 2.1:** Abra o arquivo `sales/templates/sales/pdv.html`.
- [ ] **Passo 2.2:** Localize o bloco `{% if messages %} ... {% endif %}` que está no início da tag `<main class="container-fluid py-3 h-100">` e exclua-o completamente, incluindo o script JS de `auto-dismiss` associado a ele.
- [ ] **Passo 2.3:** (Opcional, mas recomendado) Faça uma varredura (Search) no projeto por `{% if messages %}` e remova qualquer outra injeção duplicada em outros templates (como `tela_interna.html`, `login_page.html` ou outros módulos), certificando-se de que todos utilizem apenas o do `base.html`.

---

## Fase 3: Validação do Fluxo
**Objetivo:** Testar se as notificações agora respeitam o fluxo de navegação e redirecionamento.

- [ ] **Passo 3.1:** Execute a aplicação e acesse o sistema.
- [ ] **Passo 3.2:** Simule o fluxo de Abertura de Caixa.
- [ ] **Passo 3.3:** Realize o fechamento do caixa clicando no botão "Fechar Caixa" e confirme.
- [ ] **Passo 3.4:** Confirme se, ao ser redirecionado para o Dashboard (HomePage), o alerta de sucesso com o valor final do caixa aparece no topo da tela e some sozinho após 4 segundos.