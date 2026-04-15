# Plano de Ação Otimizado para Claude Code: Correção de Conflito de Testes (ImportError)

**Contexto para o Agente:**
Você está trabalhando no projeto `gesthar_pdv` (Django).
A pipeline de CI/CD (GitHub Actions) e o comando `python manage.py test` estão falhando com o seguinte erro:
`ImportError: 'tests' module incorrectly imported from '.../user/tests'. Expected '.../user'. Is this module globally installed?`

**Causa raiz:** O Django (via biblioteca `unittest`) entra em conflito de namespace quando um app possui simultaneamente um arquivo `tests.py` e um diretório `tests/` com arquivos de teste. Durante a implementação das features de RBAC e Notificações, o diretório `user/tests/` e `accounts/tests/` foram enriquecidos, mas os arquivos originais `user/tests.py` (e possivelmente de outros apps) não foram removidos/migrados adequadamente.

---
## Fase 1: Refatoração e Resolução de Conflito no App `user`
**Objetivo:** Migrar o conteúdo útil do arquivo `user/tests.py` para dentro do pacote `user/tests/` de forma organizada e remover o arquivo conflitante raiz.

- [ ] **Passo 1.1:** Abra e leia o arquivo `user/tests.py`. Identifique todas as importações, a função utilitária `make_user` e as classes `RBACPermissionTests`, `UserModelTests`, `CPFValidationTests` e `LastAdminProtectionTests`.
- [ ] **Passo 1.2:** Mova a função `make_user` e as classes `RBACPermissionTests` e `LastAdminProtectionTests` para um novo arquivo `user/tests/test_permissions.py`. Garanta que todas as importações (`TestCase`, `Client`, `reverse`, `UserGesthar`, `check_password`) sejam incluídas.
- [ ] **Passo 1.3:** Mova a classe `UserModelTests` (do antigo `tests.py`) para o arquivo já existente `user/tests/test_models.py`. Adicione-a junto à classe `UserGestharModelTests` que já existe lá. Se a função `make_user` for necessária aqui, importe-a de `user.tests.test_permissions` ou crie um arquivo `user/tests/utils.py` focado nela.
- [ ] **Passo 1.4:** Mova a classe `CPFValidationTests` para `user/tests/test_forms.py` (crie-o se não existir), garantindo o import correto de `UserGestharCreationForm`.
- [ ] **Passo 1.5:** **CRÍTICO:** Após distribuir todas as funções e classes do arquivo, EXCLUA definitivamente o arquivo `user/tests.py` (`rm user/tests.py`).

---
## Fase 2: Auditoria Preventiva em Outros Apps
**Objetivo:** Garantir que o mesmo erro de colisão de namespace não ocorra em outros apps do projeto, em especial no app `accounts`.

- [ ] **Passo 2.1:** Inspecione a raiz do app `accounts`. Verifique se existem simultaneamente o arquivo `accounts/tests.py` e o diretório `accounts/tests/`.
- [ ] **Passo 2.2:** Se houver colisão em `accounts`, crie um arquivo chamado `accounts/tests/test_legacy_raiz.py` (ou integre os testes aos arquivos corretos da pasta) e copie todo o conteúdo de `accounts/tests.py` para lá. Em seguida, exclua o arquivo original `accounts/tests.py`.
- [ ] **Passo 2.3:** Faça uma verificação rápida nos demais apps do projeto (`base`, `customer`, `product`, `sales`, `stock`, `notifications`). A regra rigorosa a ser aplicada é: **Ou o app usa APENAS o arquivo `tests.py` ou usa APENAS o diretório de pacote `tests/`. Nunca os dois juntos.**

---
## Fase 3: Validação da Suíte de Testes
**Objetivo:** Confirmar que o framework de testes voltou a realizar a varredura e descoberta normalmente.

- [ ] **Passo 3.1:** Execute no terminal: `python manage.py test user`. Certifique-se de que o Django encontra os testes divididos e que todos passam com sucesso (Status 200/OK).
- [ ] **Passo 3.2:** Execute no terminal: `python manage.py test accounts`.
- [ ] **Passo 3.3:** Por fim, rode a suíte global: `python manage.py test`. Confirme se o erro `ImportError` sumiu e se os testes são executados por completo (isso garantirá o sucesso da Action no GitHub).