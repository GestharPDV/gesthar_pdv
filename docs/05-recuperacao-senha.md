# Plano de Ação Otimizado para Claude Code: Recuperação de Senha via E-mail (Gmail)

**Contexto para o Agente:**
Você está trabalhando no projeto `gesthar_pdv` (Django, PostgreSQL, Bootstrap 5).
Sua tarefa é implementar o fluxo completo de recuperação de senha (Password Reset) utilizando o e-mail organizacional (teamgesthar@gmail.com) via SMTP TLS. Utilizaremos as views nativas do Django (`auth_views`), sobrescrevendo os templates para manter a identidade visual do projeto na pasta do app `accounts`.

---

## Fase 1: Configurações de Ambiente e E-mail (Settings)
**Objetivo:** Configurar o backend de e-mail do Django para usar o SMTP do Gmail com variáveis de ambiente.

- [ ] **Passo 1.1:** No arquivo `.env.example`, adicione as seguintes chaves de exemplo no final do arquivo:
  `EMAIL_HOST=smtp.gmail.com`
  `EMAIL_PORT=587`
  `EMAIL_USE_TLS=True`
  `EMAIL_HOST_USER=teamgesthar@gmail.com`
  `EMAIL_HOST_PASSWORD=bfjwtgfvydtopwmj`
- [ ] **Passo 1.2:** Em `core/settings.py`, adicione a configuração do backend de e-mail logo abaixo das configurações de Banco de Dados. Utilize o `os.getenv` para ler as chaves descritas acima.
- [ ] **Passo 1.3:** Ainda em `core/settings.py`, defina `DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER')`.

---

## Fase 2: Roteamento (URLs e Views Nativas)
**Objetivo:** Adicionar as rotas de recuperação de senha no app `accounts`, apontando para os templates customizados que criaremos.

- [ ] **Passo 2.1:** No arquivo `accounts/urls.py`, importe `auth_views` do pacote `django.contrib.auth`.
- [ ] **Passo 2.2:** Adicione as seguintes rotas em `urlpatterns`. Preste muita atenção aos parâmetros `template_name`, `email_template_name` e `success_url` para sobrescrever os padrões do Django, além de passar a tag `html_email_template_name` para suportar formatação rica:
  - Rota `password_reset/` usando `auth_views.PasswordResetView.as_view(...)`. O `template_name` será `accounts/password_reset_form.html`, o `email_template_name` será `accounts/password_reset_email.html` e o `success_url` será `reverse_lazy('accounts:password_reset_done')`.
  - Rota `password_reset/done/` usando `auth_views.PasswordResetDoneView.as_view(...)`. O `template_name` será `accounts/password_reset_done.html`.
  - Rota `reset/<uidb64>/<token>/` usando `auth_views.PasswordResetConfirmView.as_view(...)`. O `template_name` será `accounts/password_reset_confirm.html` e o `success_url` será `reverse_lazy('accounts:password_reset_complete')`.
  - Rota `reset/done/` usando `auth_views.PasswordResetCompleteView.as_view(...)`. O `template_name` será `accounts/password_reset_complete.html`.

---

## Fase 3: Criação das Interfaces (Templates Bootstrap 5)
**Objetivo:** Construir as telas do fluxo de esquecimento de senha mantendo a UI fluida. Todos os templates abaixo devem ficar em `accounts/templates/accounts/` e, se necessário, devem seguir a mesma estrutura base (ex: uma tela limpa centralizada semelhante ao `login_page.html`).

- [ ] **Passo 3.1:** Crie `password_reset_form.html`. Deve conter um formulário POST com um campo de e-mail (`{{ form.email }}`). Adicione um botão "Enviar E-mail de Recuperação" e um link para voltar à tela de Login.
- [ ] **Passo 3.2:** Crie `password_reset_done.html`. Exiba uma mensagem simples de sucesso: "Um e-mail foi enviado com instruções para redefinir sua senha. Verifique sua caixa de entrada e pasta de spam." e um botão voltar.
- [ ] **Passo 3.3:** Crie o template do corpo do e-mail: `password_reset_email.html`. Utilize variáveis de contexto padrão do Django (`{{ user.get_username }}`, `{{ protocol }}`, `{{ domain }}`, `{{ uid }}`, `{{ token }}`). O e-mail deve saudar o usuário e incluir um botão ou link montado com: `{{ protocol }}://{{ domain }}{% url 'accounts:password_reset_confirm' uidb64=uid token=token %}`.
- [ ] **Passo 3.4:** Crie `password_reset_subject.txt` com o assunto do e-mail. Exemplo: `Gesthar - Solicitação de Redefinição de Senha`. (Deve ter apenas uma linha).
- [ ] **Passo 3.5:** Crie `password_reset_confirm.html`. Deve conter um formulário POST exibindo os campos de nova senha (`{{ form.as_p }}` renderizado com suporte a widget_tweaks caso preferir). Trate o caso onde o token for inválido alertando o usuário (`{% if validlink %}` form `{% else %}` link inválido `{% endif %}`).
- [ ] **Passo 3.6:** Crie `password_reset_complete.html`. Exiba uma mensagem: "Sua senha foi alterada com sucesso." contendo um botão de redirecionamento para `{% url 'accounts:login' %}`.

---

## Fase 4: Ponto de Entrada (Link no Login)
**Objetivo:** Permitir que o usuário acesse o fluxo.

- [ ] **Passo 4.1:** Abra `accounts/templates/accounts/login_page.html`.
- [ ] **Passo 4.2:** Localize a área do formulário de login (logo abaixo do campo de senha) e adicione um link "Esqueceu a senha?" que aponte para `{% url 'accounts:password_reset' %}`.

---

## Fase 5: Validação Básica
**Objetivo:** Assegurar que nenhuma rota esteja quebrada.

- [ ] **Passo 5.1:** Execute `python manage.py check`.
- [ ] **Passo 5.2:** Em `accounts/tests/test_urls.py` (ou crie um se não existir), adicione um teste básico verificando se o GET para `reverse('accounts:password_reset')` retorna HTTP 200.