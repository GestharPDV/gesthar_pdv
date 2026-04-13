Com base no status atual do projeto **Gesthar**, a arquitetura adotada é a **monolítica modular do Django** (padrão MTV - *Model-Template-View*), utilizando o banco de dados **PostgreSQL**. Para atender à **Issue #48**, implementaremos um sistema de **Role-Based Access Control (RBAC)** utilizando o sistema nativo de `Groups` e `Permissions` do Django, estendendo o modelo de usuário para incluir campos específicos solicitados.

Este plano de ação foi desenhado para garantir que o sistema opere de forma segura em ambiente online, tratando *edge cases* como a inativação de usuários com histórico de vendas e a prevenção de exclusão do último administrador.

---

### Arquivo: `/docs/02-rbac-controle-acesso.md`

# Plano de Ação Otimizado para Claude Code: Controle de Acesso RBAC (Issue #48)

**Contexto para o Agente:**
Você está trabalhando no projeto `gesthar_pdv` (Django, PostgreSQL, Bootstrap 5). Sua tarefa é implementar o Módulo de Usuários e Controle de Acesso (RBAC) seguindo estritamente os requisitos funcionais  e a modelagem de dados aprovada. O sistema deve suportar dois perfis iniciais: **Administrador** e **Vendedor**.

## Fase 1: Modelo de Dados e Custom User (Core)
**Objetivo:** Implementar um `CustomUser` que herda de `AbstractUser` para incluir campos de CPF e Telefone, conforme o diagrama.

- [ ] **Passo 1.1:** Em `users/models.py`, crie a classe `User(AbstractUser)`.
    - Adicione campos: `cpf` (CharField, unique, 11 chars), `phone` (CharField), `role` (ChoiceField: ADMIN, VENDEDOR), `data_admissao` (DateField). 
    - Sobrescreva o campo `email` para ser obrigatório e único.
- [ ] **Passo 1.2:** Configure `AUTH_USER_MODEL = 'users.User'` no `settings.py`.
- [ ] **Passo 1.3:** Crie um sinal (`post_save`) para atribuir automaticamente o usuário ao respectivo `Group` (Administrador ou Vendedor) do Django baseado no campo `role`.
- [ ] **Passo 1.4:** Implementar "Soft Delete": usuários nunca são excluídos do banco para manter a integridade de vendas passadas; use o campo `is_active=False`. 

## Fase 2: Autenticação e Segurança de Sessão
**Objetivo:** Garantir que o processo de login seja robusto e protegido contra ataques comuns.

- [ ] **Passo 2.1:** Em `users/views.py`, utilize `LoginView` nativa, mas adicione lógica de **Rate Limiting** (limite de tentativas) para prevenir Brute Force.
- [ ] **Passo 2.2:** Configure o `settings.py` para segurança em produção:
    - `SESSION_COOKIE_SECURE = True`
    - `CSRF_COOKIE_SECURE = True`
    - `SESSION_EXPIRE_AT_BROWSER_CLOSE = True`
    - `LOGIN_URL = 'users:login'`
- [ ] **Passo 2.3:** Implemente a funcionalidade de "Recuperação de Senha" utilizando o fluxo de `PasswordResetView` do Django com envio de e-mail via SMTP. 

## Fase 3: Camada de Autorização (Mixins e Decorators)
**Objetivo:** Criar travas de segurança para que vendedores não acessem módulos sensíveis (Financeiro/Relatórios).

- [ ] **Passo 3.1:** Crie `users/permissions.py` com o mixin `AdminRequiredMixin`.
    - Use `UserPassesTestMixin` para validar se `user.role == 'ADMIN'`.
- [ ] **Passo 3.2:** Aplique o `LoginRequiredMixin` em todas as Views do sistema.
- [ ] **Passo 3.3:** Implemente um Log de Atividades simples em `users/models.py` (tabela `UserActionLog`) para registrar: quem, quando e qual ação realizou (ex: "Cancelamento de Venda").

## Fase 4: Interface de Gerenciamento (Templates)
**Objetivo:** Renderizar as telas de cadastro e listagem conforme os protótipos.

- [ ] **Passo 4.1:** Crie `users/templates/users/user_form.html` (Cadastro/Edição).
    - Utilize `django-crispy-forms` com Bootstrap 5.
    - **Edge Case:** Impeça que um usuário logado desative a si próprio ou altere seu próprio cargo se ele for o único Admin.
- [ ] **Passo 4.2:** Crie `users/templates/users/user_list.html` (Visualização).
    - Exiba status (Ativo/Inativo) com badges coloridos.
- [ ] **Passo 4.3:** No `base/sidebar.html`, utilize as tags de template `{% if user.role == 'ADMIN' %}` para esconder menus de Relatórios Financeiros e Gestão de Usuários de quem for Vendedor.

## Fase 5: Validação e Segurança
**Objetivo:** Certificar a integridade do RBAC.

- [ ] **Passo 5.1:** Em `users/tests.py`, crie testes para:
    - Garantir que um Vendedor recebe status 403 ao tentar acessar `/usuarios/cadastrar/`.
    - Validar que senhas não são salvas em texto plano no banco.
    - Validar que o CPF aceita apenas 11 dígitos e é único.
- [ ] **Passo 5.2:** Verifique se o comando `python manage.py createsuperuser` ainda funciona com o novo modelo customizado.

---

### Considerações de Engenharia:
1.  **Integridade Referencial:** Como o `Usuario` está ligado a `Venda`  e `Caixa`, o Claude deve ser instruído a **bloquear a deleção física** (`models.PROTECT`) no banco de dados.
2.  **Padrão de UI:** Use os ícones de "olho" para visualização e "lápis" para edição, mantendo a consistência visual dos protótipos de produtos e clientes.
