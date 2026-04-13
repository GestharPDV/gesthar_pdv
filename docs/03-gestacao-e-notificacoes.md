# Plano de Ação: Evolução Gestacional e Notificações (Via Login Trigger)

**Contexto para o Agente:**
O objetivo é transformar a data estática de parto em um monitoramento ativo. O sistema deve calcular a semana gestacional atual e alertar a equipe via notificações internas no Dashboard. A verificação de milestones deve ocorrer no **primeiro login do dia** de qualquer usuário, utilizando Signals e Cache para evitar sobrecarga.

## Fase 1: Inteligência no Modelo de Cliente (`customers`)
**Objetivo:** Implementar lógica dinâmica de semanas.

- [ ] **Passo 1.1:** No arquivo `customers/models.py`, atualize o modelo `Client`.
    - Implemente uma `@property` chamada `current_weeks`:
      ```python
      # Lógica: (Hoje - (Data Prevista - 280 dias)) / 7
      ```
    - Adicione a `@property` `gestational_stage` para diferenciar "Gestante" de "Pós-parto" (se hoje > DPP).
- [ ] **Passo 1.2:** Adicione validação no método `clean()` para garantir que a `data_prevista_parto` não seja uma data impossível (ex: mais de 42 semanas no passado ou futuro).

## Fase 2: Infraestrutura de Notificações (`notifications`)
**Objetivo:** Criar o armazenamento dos alertas.

- [ ] **Passo 2.1:** Crie o app `notifications` e o modelo `Notification`:
    - `user`: ForeignKey(User) -> Destinatário do alerta.
    - `client`: ForeignKey(Client) -> Cliente vinculada ao marco.
    - `message`: CharField -> Ex: "Fulana atingiu 35 semanas! Oferecer enxoval."
    - `milestone_key`: String (ex: '35_weeks', 'post_partum') -> Para evitar duplicatas.
    - `is_read`: Boolean (default=False).
- [ ] **Passo 2.2:** Crie `notifications/services.py` com a função `run_milestone_check()`:
    - Filtre clientes ativas.
    - Gere notificações apenas se o marco (35 semanas ou pós-parto) for atingido e **ainda não existir** uma notificação não lida para aquele `milestone_key` e cliente.

## Fase 3: Gatilho de Execução no Login (`users`)
**Objetivo:** Disparar a checagem de forma otimizada.

- [ ] **Passo 3.1:** Em `users/signals.py`, implemente o receptor para `user_logged_in`.
- [ ] **Passo 3.2:** Utilize o Cache do Django para garantir a execução única diária:
    ```python
    if not cache.get('last_milestone_check'):
        run_milestone_check()
        cache.set('last_milestone_check', True, 86400) # Expira em 24h
    ```
- [ ] **Passo 3.3:** Certifique-se de que o `users/apps.py` importa os signals no método `ready()`.

## Fase 4: Interface e Visualização (UI/UX)
**Objetivo:** Exibir os alertas para Admins e Vendedores.

- [ ] **Passo 4.1:** Crie um `context_processor.py` para injetar `unread_notifications_count` globalmente.
- [ ] **Passo 4.2:** No `base/sidebar.html`, adicione um badge numérico no ícone de notificações.
- [ ] **Passo 4.3:** No Dashboard (`home.html`), liste as 5 notificações mais recentes com link direto para o WhatsApp da cliente.

## Fase 5: Segurança e Performance
- [ ] **Passo 5.1:** Use `select_related('client')` na busca de notificações para evitar o problema N+1.
- [ ] **Passo 5.2:** Implemente uma View simples `MarkNotificationReadView` para que o usuário possa dar "baixa" no alerta.

## Testes de Aceitação
1. **Idempotência:** Logar com dois usuários diferentes no mesmo dia e verificar se a função de checagem rodou apenas uma vez (verificar via logs ou timestamp do cache).
2. **Cálculo:** Criar cliente com DPP para daqui a exatas 5 semanas e confirmar se o alerta de "35 semanas" é gerado.
3. **Persistência:** Garantir que, se uma notificação de "35 semanas" já existe, o sistema não crie outra igual no dia seguinte.