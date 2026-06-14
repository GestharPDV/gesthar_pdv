# Plano de Ação: Ajustar Divergência de Valor de Pagamento Após Desconto

**Contexto para o Agente:**
Você está trabalhando no projeto `gesthar_pdv` (Django, PostgreSQL, Bootstrap 5). Sua tarefa é corrigir um *bug* crítico no módulo de Vendas (PDV). Atualmente, quando um desconto é aplicado a uma venda, o sistema registra e envia para a etapa de pagamento o valor cheio (subtotal dos itens), ignorando o desconto concedido. Você deve garantir que a regra de negócio seja respeitada de ponta a ponta: do cálculo no JavaScript do front-end até a validação e persistência no back-end.

---

## Fase 1: Revisão da Regra de Negócio no Backend (Models)
**Objetivo:** Garantir que o modelo de Venda tenha uma fonte única de verdade para o valor final a ser cobrado.

- [ ] **Passo 1.1:** Abra `sales/models.py` e localize o modelo responsável pela venda (ex: `Sale` ou `Venda`).
- [ ] **Passo 1.2:** Verifique a existência dos campos `subtotal` (soma dos itens), `desconto` (valor absoluto ou percentual) e `valor_total` (valor final).
- [ ] **Passo 1.3:** Se não existir, implemente uma propriedade (`@property`) chamada `valor_final_com_desconto` que retorne `self.subtotal - self.desconto` (ou a lógica equivalente baseada no tipo de desconto).
- [ ] **Passo 1.4:** Certifique-se de que o método `save()` ou a função que finaliza a venda atualize o campo de valor final a ser pago utilizando esta propriedade, garantindo que o banco de dados reflita o valor real.

---

## Fase 2: Ajuste de UI e Reatividade no Frontend (Templates e JS)
**Objetivo:** Corrigir a interface do PDV para que o usuário veja o valor correto em tempo real e para que o *payload* enviado ao backend contenha os dados atualizados.

- [ ] **Passo 2.1:** Abra o template principal do PDV (geralmente `sales/templates/sales/pdv.html` ou `sales/templates/sales/close_register.html`).
- [ ] **Passo 2.2:** Localize o script JavaScript que gerencia o carrinho de compras e o cálculo dos totais (ex: funções como `calculateTotal()`, `updateCart()`).
- [ ] **Passo 2.3:** Ajuste a lógica matemática no JavaScript: ao inserir um valor no input de desconto, o sistema deve abater esse valor do `subtotal` e atualizar o elemento HTML correspondente ao "Total a Pagar" (`innerText` ou `innerHTML`).
- [ ] **Passo 2.4:** **Ponto Crítico:** Garanta que o valor final enviado no formulário de *checkout* (seja via *input hidden* ou requisição AJAX/Fetch API) represente o valor já com o desconto aplicado, ou garanta que os campos `subtotal` e `desconto` sejam enviados separadamente para recálculo no backend.

---

## Fase 3: Sincronização e Validação do Checkout (Views)
**Objetivo:** Prevenir que manipulações no frontend gerem cobranças indevidas, recalculando e validando os valores no momento de fechar a venda.

- [ ] **Passo 3.1:** Abra `sales/views.py` e localize a View responsável pela finalização da venda/pagamento (ex: `CheckoutView`, `process_payment`, ou similar).
- [ ] **Passo 3.2:** Adicione uma camada de validação estrita antes de criar o registro de pagamento:
    - Recalcule o subtotal iterando sobre os itens do carrinho enviados.
    - Subtraia o desconto informado na requisição.
    - Verifique se o `valor_pago` recebido bate exatamente com a fórmula: `(Soma dos Itens) - Desconto`.
- [ ] **Passo 3.3:** Se o sistema possuir integração com métodos de pagamento específicos (ex: salvar em `PagamentoVenda` ou repassar para um gateway), certifique-se de passar o valor recalculado (`valor_final_com_desconto`), e não o subtotal.

---

## Fase 4: Validação e Prevenção de Regressão (Testes)
**Objetivo:** Criar testes automatizados para garantir que descontos nunca mais sejam ignorados no momento do pagamento.

- [ ] **Passo 4.1:** Abra `sales/tests.py`.
- [ ] **Passo 4.2:** Crie um método de teste (ex: `test_venda_com_desconto_aplica_valor_correto_no_pagamento`) que simule o fluxo completo:
    - Crie um produto teste.
    - Adicione o produto ao carrinho (simulando a requisição).
    - Aplique um desconto válido.
    - Envie o *payload* de finalização da venda.
- [ ] **Passo 4.3:** Faça asserções (`self.assertEqual`) para verificar se o objeto de venda salvo no banco possui o `valor_total` igual ao preço do produto subtraído do desconto.
- [ ] **Passo 4.4:** Se houver modelo de controle de Caixa/Movimentação, valide também se a entrada financeira registrada corresponde ao valor com desconto.

---

### Considerações de Engenharia:
1. **Tipagem e Precisão:** Em Python, garanta que os cálculos de desconto utilizem `Decimal` (do módulo `decimal`) em vez de `float` para evitar erros de arredondamento financeiro. No banco de dados, os campos devem ser `DecimalField`.
2. **Segurança (Zero Trust):** O backend **nunca** deve confiar cegamente no valor final enviado pelo frontend. O JavaScript serve apenas para feedback visual; o recálculo e a aplicação do desconto *devem* ocorrer na View ou na camada de Serviço (`sales/services.py`) antes de salvar. Limitadores de desconto máximo (ex: "não pode descontar mais que o subtotal") devem ser aplicados.