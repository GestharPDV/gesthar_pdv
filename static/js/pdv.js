(function () {
    'use strict';

    const config = document.getElementById('pdv-config').dataset;

    function getCsrf() {
        return config.csrfToken;
    }

    // ---- Estado Mercado Pago Point ----
    let mpOrderId = null;
    let mpMethod = null;
    let mpAmount = 0;
    let mpPollInterval = null;
    let mpPayerCosts = [];
    let mpBaseAmount = 0;

    document.addEventListener('DOMContentLoaded', function () {
        initSearchFocus();
        initDiscountInputs();
        initItemDiscountListeners();
        initProductSearch();
        initPaymentModal();
    });

    document.addEventListener('keydown', handleGlobalKeydown);

    // ---- Foco inicial ----

    function initSearchFocus() {
        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.focus();
    }

    // ---- Atalhos de teclado globais ----

    function handleGlobalKeydown(event) {
        if (event.key === 'F2') {
            event.preventDefault();
            const btnFinalizar = document.getElementById('btn-finalizar');
            if (btnFinalizar && !btnFinalizar.disabled) btnFinalizar.click();
        }
        if (event.key === '/' || event.key === 'F1') {
            event.preventDefault();
            const searchInput = document.getElementById('search-input');
            if (searchInput) searchInput.focus();
        }
    }

    // ---- Inputs de desconto do rodapé ----

    function initDiscountInputs() {
        const inputDiscReal = document.getElementById('footer-disc-real');
        const inputDiscPercent = document.getElementById('footer-disc-percent');
        let discountDebounce;

        function scheduleDiscountSave() {
            clearTimeout(discountDebounce);
            discountDebounce = setTimeout(saveDiscountToBackend, 600);
        }

        if (inputDiscReal && inputDiscPercent) {
            inputDiscReal.addEventListener('input', function () {
                if (this.value > 0) inputDiscPercent.value = '';
                recalculateSaleTotal();
                scheduleDiscountSave();
            });
            inputDiscPercent.addEventListener('input', function () {
                if (this.value > 0) inputDiscReal.value = '';
                recalculateSaleTotal();
                scheduleDiscountSave();
            });
        }
    }

    function initItemDiscountListeners() {
        document.querySelectorAll('.product-list tbody .item-discount-input').forEach(input => {
            input.addEventListener('input', function () {
                updateItemDiscount(this);
            });
        });
    }

    function getCurrentDiscountAbsolute() {
        const inputDiscReal = document.getElementById('footer-disc-real');
        const inputDiscPercent = document.getElementById('footer-disc-percent');
        const discReal = parseFloat(inputDiscReal.value.replace(',', '.')) || 0;
        const discPercent = parseFloat(inputDiscPercent.value.replace(',', '.')) || 0;

        if (discReal > 0) return discReal;

        if (discPercent > 0) {
            let brutSum = 0;
            document.querySelectorAll('.product-list tbody tr').forEach(row => {
                if (row.querySelector('td:nth-child(2)') === null) return;
                const unitPrice = parseFloat(row.querySelector('td:nth-child(3)').innerText.replace('R$', '').replace(',', '.').trim()) || 0;
                const quantity = parseInt(row.querySelector('td:nth-child(2)').innerText) || 0;
                brutSum += unitPrice * quantity;
            });
            return brutSum * (discPercent / 100);
        }
        return 0;
    }

    async function saveDiscountToBackend() {
        const discountAbsolute = getCurrentDiscountAbsolute();
        const formData = new FormData();
        formData.append('discount_amount', discountAbsolute.toFixed(2));
        formData.append('csrfmiddlewaretoken', getCsrf());

        try {
            const response = await fetch(config.applyDiscountUrl, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            const data = await response.json();
            if (response.ok && data.success) {
                const modalRemaining = document.getElementById('modal-remaining-balance');
                if (modalRemaining) {
                    modalRemaining.innerText = 'R$ ' + data.remaining_balance.toFixed(2).replace('.', ',');
                }
            }
        } catch (e) {
            // silencioso — erro será detectado na abertura do modal
        }
    }

    function updateItemDiscount(input) {
        const discountValue = parseFloat(input.value.replace(',', '.')) || 0;
        const unitPrice = parseFloat(input.dataset.unitPrice) || 0;
        const quantity = parseInt(input.dataset.quantity) || 1;
        const itemTotal = unitPrice * quantity;

        if (discountValue > itemTotal) {
            alert('O desconto não pode ser maior que o valor total do item!');
            input.value = (0).toFixed(2);
            return;
        }

        const totalCell = input.closest('tr').querySelector('td:nth-child(5)');
        totalCell.innerText = 'R$ ' + Math.max(itemTotal - discountValue, 0).toFixed(2).replace('.', ',');
        recalculateSaleTotal();
    }

    function recalculateSaleTotal() {
        let subtotalVenda = 0;
        const inputDiscReal = document.getElementById('footer-disc-real');
        const inputDiscPercent = document.getElementById('footer-disc-percent');
        const displaySubtotal = document.getElementById('display-subtotal');
        const displayTotalGeral = document.getElementById('display-total-geral');

        const discGlobalReal = parseFloat(inputDiscReal.value.replace(',', '.')) || 0;
        const discGlobalPercent = parseFloat(inputDiscPercent.value.replace(',', '.')) || 0;

        document.querySelectorAll('.product-list tbody tr').forEach(row => {
            if (row.innerText.includes("Nenhum item")) return;
            const unitPrice = parseFloat(row.querySelector('td:nth-child(3)').innerText.replace('R$', '').replace(',', '.').trim());
            const quantity = parseInt(row.querySelector('td:nth-child(2)').innerText);
            const discItem = parseFloat(row.querySelector('td:nth-child(4) input').value.replace(',', '.')) || 0;
            let totalLinha = (unitPrice * quantity) - discItem;

            if (discGlobalPercent > 0) {
                totalLinha = totalLinha * (1 - (discGlobalPercent / 100));
            }

            row.querySelector('td:nth-child(5)').innerText = 'R$ ' + totalLinha.toFixed(2).replace('.', ',');
            subtotalVenda += (unitPrice * quantity) - discItem;
        });

        let totalFinal = subtotalVenda;
        if (discGlobalReal > 0) {
            totalFinal -= discGlobalReal;
        } else if (discGlobalPercent > 0) {
            totalFinal = subtotalVenda * (1 - (discGlobalPercent / 100));
        }
        if (totalFinal < 0) totalFinal = 0;

        displaySubtotal.innerText = 'R$ ' + subtotalVenda.toFixed(2).replace('.', ',');
        displayTotalGeral.innerText = 'R$ ' + totalFinal.toFixed(2).replace('.', ',');

        const modalInput = document.getElementById('payment-amount-input');
        if (modalInput) modalInput.value = totalFinal.toFixed(2);
    }

    // ---- Busca de produtos via API ----

    function initProductSearch() {
        const searchInput = document.getElementById('search-input');
        const resultsContainer = document.getElementById('search-results');
        if (!searchInput || !resultsContainer) return;

        let timeoutId;

        function closeResults() {
            resultsContainer.style.display = 'none';
            resultsContainer.innerHTML = '';
        }

        searchInput.addEventListener('input', function () {
            const query = this.value;
            clearTimeout(timeoutId);

            if (query.length < 3) {
                closeResults();
                return;
            }

            timeoutId = setTimeout(() => {
                fetch(`${config.apiSearchUrl}?term=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        resultsContainer.innerHTML = '';
                        if (data.length > 0) {
                            resultsContainer.style.display = 'block';
                            const ul = document.createElement('ul');
                            ul.className = 'list-group list-group-flush';
                            data.forEach(item => {
                                const li = document.createElement('li');
                                li.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
                                li.style.cursor = 'pointer';
                                li.innerHTML = `
                                    <div>
                                        <div class="fw-semibold text-body">${item.label}</div>
                                        <small class="text-muted">SKU: ${item.value}</small>
                                    </div>
                                    <span class="fw-bold text-success">R$ ${item.price.toFixed(2)}</span>
                                `;
                                li.addEventListener('click', function () {
                                    searchInput.value = item.value;
                                    closeResults();
                                });
                                ul.appendChild(li);
                            });
                            resultsContainer.appendChild(ul);
                        } else {
                            closeResults();
                        }
                    })
                    .catch(error => console.error('Erro na busca:', error));
            }, 300);
        });

        document.addEventListener('click', function (e) {
            if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
                closeResults();
            }
        });
    }

    // ---- Modal de pagamento ----

    function initPaymentModal() {
        const paymentModalElement = document.getElementById('paymentModal');
        if (!paymentModalElement) return;

        const paymentModal = new bootstrap.Modal(paymentModalElement);
        const btnOpenModal = document.getElementById('btnOpenPayment');
        const detailArea = document.getElementById('payment-detail-area');

        paymentModalElement.addEventListener('hidden.bs.modal', function () {
            document.getElementById('step-payment-select').style.display = 'block';
            document.getElementById('step-receipt').classList.add('d-none');
            document.getElementById('step-success').classList.add('d-none');
            detailArea.innerHTML = '<div class="py-5 text-muted opacity-50"><span class="material-symbols-outlined fs-1">payments</span><p>Aguardando seleção...</p></div>';
            stopMpPolling();
            mpOrderId = null;
            mpMethod = null;
            mpAmount = 0;
            mpPayerCosts = [];
            mpBaseAmount = 0;
        });

        btnOpenModal.addEventListener('click', async function () {
            const totalVenda = parseFloat(document.getElementById('display-total-geral').innerText.replace('R$', '').replace(',', '.'));
            if (totalVenda <= 0) {
                alert("O valor da venda deve ser maior que zero!");
                return;
            }

            const discountAbsolute = getCurrentDiscountAbsolute();
            if (discountAbsolute > 0) {
                const formData = new FormData();
                formData.append('discount_amount', discountAbsolute.toFixed(2));
                formData.append('csrfmiddlewaretoken', getCsrf());

                try {
                    const response = await fetch(config.applyDiscountUrl, {
                        method: 'POST',
                        body: formData,
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    });
                    const data = await response.json();
                    if (!response.ok || !data.success) {
                        alert('Erro ao aplicar desconto: ' + (data.error || 'Erro desconhecido'));
                        return;
                    }
                    document.getElementById('modal-remaining-balance').innerText = 'R$ ' + data.remaining_balance.toFixed(2).replace('.', ',');
                } catch (e) {
                    alert('Erro ao comunicar com o servidor. Tente novamente.');
                    return;
                }
            }

            paymentModal.show();
        });

        document.querySelectorAll('.btn-payment-option').forEach(btn => {
            btn.addEventListener('click', function () {
                const method = this.dataset.method;
                const isMp = method.endsWith('_mp');
                const baseMethod = method.replace('_mp', '');

                document.querySelectorAll('.btn-payment-option').forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                const valorRestanteStr = document.getElementById('modal-remaining-balance').innerText.replace('R$', '').replace(',', '.').trim();
                const valorCalculado = parseFloat(valorRestanteStr).toFixed(2);

                if (isMp) {
                    const isCredit = baseMethod === 'CREDITO';

                    detailArea.innerHTML = `
                        <div class="p-4 rounded bg-light border border-2 border-info">
                            <div class="mb-3">
                                <span class="material-symbols-outlined fs-1" style="color: #009ee3;">contactless</span>
                            </div>
                            <p class="fw-bold text-muted mb-3">MERCADO PAGO POINT</p>
                            <label class="small fw-bold text-muted mb-2 d-block">VALOR A RECEBER</label>
                            <div class="input-group mb-3">
                                <span class="input-group-text">R$</span>
                                <input type="number" id="payment-amount-input" class="form-control form-control-lg fw-bold" value="${valorCalculado}" min="0.01" max="${valorCalculado}" step="0.01">
                            </div>
                            ${isCredit ? `
                            <label class="small fw-bold text-muted mb-2 d-block">PARCELAS</label>
                            <select id="mp-installments" class="form-select form-select-lg mb-3">
                                <option>Carregando...</option>
                            </select>
                            <label class="small fw-bold text-muted mb-2 d-block">QUEM PAGA A TAXA DO PARCELAMENTO?</label>
                            <div class="btn-group w-100 mb-3" role="group">
                                <input type="radio" class="btn-check" name="mp-fee-payer" id="mp-fee-seller" value="false" checked>
                                <label class="btn btn-outline-secondary" for="mp-fee-seller">Vendedor</label>
                                <input type="radio" class="btn-check" name="mp-fee-payer" id="mp-fee-buyer" value="true">
                                <label class="btn btn-outline-info" for="mp-fee-buyer">Cliente</label>
                            </div>` : ''}
                            <label class="small fw-bold text-muted mb-2 d-block">TEMPO DE EXPIRAÇÃO</label>
                            <select id="mp-expiration" class="form-select form-select-lg mb-3">
                                <option value="PT1M">1 minuto</option>
                                <option value="PT5M">5 minutos</option>
                                <option value="PT10M">10 minutos</option>
                                <option value="PT16M" selected>16 minutos (padrão)</option>
                                <option value="PT30M">30 minutos</option>
                                <option value="PT1H">1 hora</option>
                            </select>
                            <div class="d-flex gap-2 mb-2">
                                <button class="btn flex-grow-1 py-3 fw-bold" style="background-color:#009ee3;color:white;border:none;" onclick="confirmPayment('${method}')">
                                    ENVIAR PARA TERMINAL
                                </button>
                                <button class="btn btn-outline-danger py-3 fw-bold" id="btn-cancel-order" disabled onclick="cancelMercadoPagoOrder()">
                                    CANCELAR ORDER
                                </button>
                            </div>
                            <button class="btn btn-success w-100 py-2 fw-bold" id="btn-mp-continue" style="display:none;" onclick="proceedMercadoPagoFlow()">
                                PAGAMENTO CONCLUÍDO NO TERMINAL
                            </button>
                            <button class="btn btn-warning w-100 py-2 fw-bold mt-1" id="btn-mp-simulate" style="display:none;" onclick="simulateMpApproval()">
                                SIMULAR APROVAÇÃO (TESTE)
                            </button>
                        </div>
                    `;

                    if (isCredit) {
                        mpPayerCosts = [];
                        const amtInput = document.getElementById('payment-amount-input');
                        mpBaseAmount = parseFloat(amtInput.value) || 0;
                        loadMpInstallments(mpBaseAmount);

                        amtInput.addEventListener('input', () => {
                            mpBaseAmount = parseFloat(amtInput.value) || 0;
                            renderInstallmentOptions(mpBaseAmount);
                        });

                                        document.querySelectorAll('input[name="mp-fee-payer"]').forEach(radio => {
                            radio.addEventListener('change', () => {
                                renderInstallmentOptions(mpBaseAmount);
                            });
                        });
                    }

                } else if (method === 'PIX') {
                    detailArea.innerHTML = `
                        <div id="qr-code-placeholder" class="mb-3">
                            <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=PagamentoPDV" alt="QR Code">
                        </div>
                        <p class="fw-bold text-muted small">ESCANEIE O QR-CODE</p>
                        <input type="hidden" id="payment-amount-input" value="${valorCalculado}">
                        <button class="btn botao-verde w-100 mt-3 py-2 fw-bold" onclick="confirmPayment('PIX')">CONFIRMAR PIX</button>
                    `;
                } else {
                    detailArea.innerHTML = `
                        <div class="p-4 rounded border border-dashed" style="background-color: var(--bg-card);">
                            <label class="small fw-bold text-muted mb-2 d-block">VALOR A RECEBER</label>
                            <div class="input-group">
                                <span class="input-group-text">R$</span>
                                <input type="number" id="payment-amount-input" class="form-control form-control-lg fw-bold" value="${valorCalculado}" min="0.01" step="0.01">
                            </div>
                            <button class="btn botao-rosa w-100 mt-4 py-3 fw-bold" onclick="confirmPayment('${method}')">CONFIRMAR PAGAMENTO</button>
                        </div>
                    `;
                }
            });
        });
    }

    async function confirmPayment(method) {
        const btn = event.target;
        const amountInput = document.getElementById('payment-amount-input');
        const statusAlert = document.getElementById('payment-status-alert');
        const amount = amountInput?.value || "0.00";
        const isMp = method.endsWith('_mp');
        const baseMethod = method.replace('_mp', '');

        // ---- Fluxo Mercado Pago Point ----
        if (isMp) {
            if (!amountInput.value || parseFloat(amountInput.value) <= 0) {
                amountInput.value = parseFloat(
                    document.getElementById('modal-remaining-balance').innerText.replace('R$', '').replace(',', '.').trim()
                ).toFixed(2);
            }

            const installments = document.getElementById('mp-installments')?.value || '1';
            const expiration = document.getElementById('mp-expiration')?.value || 'PT16M';
            const buyerPaysFee = document.querySelector('input[name="mp-fee-payer"]:checked')?.value === 'true';

            statusAlert.innerText = 'Enviando para o terminal...';
            statusAlert.classList.remove('d-none', 'alert-danger', 'alert-success');
            statusAlert.classList.add('alert-warning');

            const formData = new FormData();
            formData.append('amount', parseFloat(amountInput.value).toFixed(2));
            formData.append('sale_id', config.salePk);
            formData.append('installments', installments);
            formData.append('expiration_time', expiration);
            formData.append('buyer_pays_fee', buyerPaysFee ? 'true' : 'false');
            formData.append('csrfmiddlewaretoken', getCsrf());

            try {
                const resp = await fetch(config.mpCreateOrderUrl, {
                    method: 'POST', body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await resp.json();

                if (resp.ok && data.success) {
                    mpOrderId = data.order?.id || null;
                    mpMethod = baseMethod;
                    mpAmount = parseFloat(amountInput.value);

                    if (!mpOrderId) throw new Error('Order criada sem ID na resposta do MP.');

                    const btnCancel = document.getElementById('btn-cancel-order');
                    const btnContinue = document.getElementById('btn-mp-continue');
                    const btnSimulate = document.getElementById('btn-mp-simulate');
                    if (btnCancel) btnCancel.disabled = false;
                    if (btnContinue) btnContinue.style.display = 'block';
                    if (btnSimulate) btnSimulate.style.display = 'block';

                    startMpPolling();

                    let msg = `✓ ORDER ${mpOrderId} ENVIADA. Aguarde na maquininha.`;
                    if (baseMethod === 'CREDITO') {
                        msg += `\n${installments}x de R$ ${(mpAmount / parseInt(installments)).toFixed(2)}`;
                    }
                    statusAlert.innerText = msg;
                    statusAlert.classList.remove('alert-warning');
                    statusAlert.classList.add('alert-success');
                } else {
                    throw new Error(data.error || JSON.stringify(data.details) || 'Erro ao criar order MP');
                }
            } catch (err) {
                statusAlert.innerText = 'ERRO: ' + err.message;
                statusAlert.classList.remove('d-none', 'alert-warning', 'alert-success');
                statusAlert.classList.add('alert-danger');
            }
            return;
        }

        // ---- Fluxo pagamento normal ----
        btn.disabled = true;
        const originalText = btn.innerText;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> PROCESSANDO...`;
        statusAlert.classList.add('d-none');

        const formData = new FormData();
        formData.append('method', method);
        formData.append('amount', amount);
        formData.append('csrfmiddlewaretoken', getCsrf());

        try {
            const response = await fetch(config.addPaymentUrl, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                const remainingLabel = document.querySelector('#step-payment-select .h4');
                remainingLabel.innerText = 'R$ ' + data.remaining.toFixed(2).replace('.', ',');

                if (data.remaining > 0) {
                    statusAlert.innerText = `PAGAMENTO PARCIAL REGISTRADO! FALTA: R$ ${data.remaining.toFixed(2).replace('.', ',')}`;
                    statusAlert.classList.remove('d-none');
                    amountInput.value = data.remaining.toFixed(2);
                    btn.disabled = false;
                    btn.innerText = originalText;
                } else {
                    showChangeScreen(data.change);
                }
            } else {
                throw new Error(data.error || "Erro desconhecido");
            }
        } catch (error) {
            statusAlert.innerText = "ERRO: " + error.message;
            statusAlert.classList.remove('d-none', 'alert-info');
            statusAlert.classList.add('alert-danger');
            btn.disabled = false;
            btn.innerText = originalText;
        }
    }

    function showChangeScreen(changeAmount) {
        document.getElementById('step-payment-select').style.display = 'none';
        const stepChange = document.getElementById('step-change');
        stepChange.classList.remove('d-none');

        const changeDisplay = document.getElementById('change-display');
        const noChangeDisplay = document.getElementById('no-change-display');

        if (changeAmount > 0) {
            changeDisplay.classList.remove('d-none');
            noChangeDisplay.classList.add('d-none');
            changeDisplay.querySelector('h1').innerText = 'R$ ' + changeAmount.toFixed(2).replace('.', ',');
        } else {
            changeDisplay.classList.add('d-none');
            noChangeDisplay.classList.remove('d-none');
        }

        const handleEnter = (e) => {
            if (e.key === 'Enter') {
                document.removeEventListener('keydown', handleEnter);
                goToReceipt();
            }
        };
        document.addEventListener('keydown', handleEnter);
    }

    function goToReceipt() {
        document.getElementById('step-change').classList.add('d-none');
        document.getElementById('step-receipt').classList.remove('d-none');
    }

    function finishFlow(choice) {
        document.getElementById('step-receipt').style.display = 'none';
        document.getElementById('step-success').classList.remove('d-none');

        const enterFinalizer = (e) => {
            if (e.key === 'Enter') {
                document.removeEventListener('keydown', enterFinalizer);
                const finalForm = document.createElement('form');
                finalForm.method = 'POST';
                finalForm.action = config.completeSaleUrl;
                const csrf = document.createElement('input');
                csrf.type = 'hidden';
                csrf.name = 'csrfmiddlewaretoken';
                csrf.value = getCsrf();
                finalForm.appendChild(csrf);
                document.body.appendChild(finalForm);
                finalForm.submit();
            }
        };
        document.addEventListener('keydown', enterFinalizer);
    }

    // ---- Mercado Pago: concluir pagamento ----

    async function proceedMercadoPagoFlow() {
        if (!mpOrderId || !mpMethod || !mpAmount) {
            alert('Nenhum pagamento MP pendente.');
            return;
        }
        stopMpPolling();

        const statusAlert = document.getElementById('payment-status-alert');
        const formData = new FormData();
        formData.append('method', mpMethod);
        formData.append('amount', mpAmount.toFixed(2));
        formData.append('csrfmiddlewaretoken', getCsrf());

        try {
            const response = await fetch(config.addPaymentUrl, {
                method: 'POST', body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            const data = await response.json();

            if (!(response.ok && data.success)) throw new Error(data.error || 'Erro ao registrar pagamento.');

            const remainingLabel = document.querySelector('#step-payment-select .h4');
            remainingLabel.innerText = 'R$ ' + data.remaining.toFixed(2).replace('.', ',');

            if (data.remaining > 0) {
                statusAlert.innerText = `PARCIAL REGISTRADO! FALTA: R$ ${data.remaining.toFixed(2).replace('.', ',')}`;
                statusAlert.classList.remove('d-none', 'alert-danger');
                statusAlert.classList.add('alert-success');
                mpOrderId = null; mpMethod = null; mpAmount = 0;
                const btnCancel = document.getElementById('btn-cancel-order');
                const btnContinue = document.getElementById('btn-mp-continue');
                const btnSimulate = document.getElementById('btn-mp-simulate');
                if (btnCancel) btnCancel.disabled = true;
                if (btnContinue) btnContinue.style.display = 'none';
                if (btnSimulate) btnSimulate.style.display = 'none';
            } else {
                showChangeScreen(data.change || 0);
            }
        } catch (error) {
            statusAlert.innerText = 'ERRO: ' + error.message;
            statusAlert.classList.remove('d-none', 'alert-success', 'alert-warning');
            statusAlert.classList.add('alert-danger');
        }
    }

    // ---- Mercado Pago: cancelar order ----

    async function cancelMercadoPagoOrder() {
        if (!mpOrderId) { alert('Nenhuma order ativa.'); return; }
        if (!confirm(`Cancelar a order ${mpOrderId}?`)) return;
        stopMpPolling();

        const statusAlert = document.getElementById('payment-status-alert');
        statusAlert.innerText = 'Cancelando order...';
        statusAlert.classList.remove('d-none', 'alert-danger', 'alert-success');
        statusAlert.classList.add('alert-warning');

        const formData = new FormData();
        formData.append('order_id', mpOrderId);
        formData.append('csrfmiddlewaretoken', getCsrf());

        try {
            const resp = await fetch(config.mpCancelOrderUrl, {
                method: 'POST', body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            const data = await resp.json();

            if (resp.ok && data.success) {
                statusAlert.innerText = `✓ ORDER ${mpOrderId} CANCELADA`;
                statusAlert.classList.remove('alert-warning');
                statusAlert.classList.add('alert-success');
                mpOrderId = null; mpMethod = null; mpAmount = 0;
                const btnCancel = document.getElementById('btn-cancel-order');
                const btnContinue = document.getElementById('btn-mp-continue');
                const btnSimulate = document.getElementById('btn-mp-simulate');
                if (btnCancel) btnCancel.disabled = true;
                if (btnContinue) btnContinue.style.display = 'none';
                if (btnSimulate) btnSimulate.style.display = 'none';
            } else {
                throw new Error(data.error || 'Erro ao cancelar order');
            }
        } catch (err) {
            statusAlert.innerText = 'ERRO AO CANCELAR: ' + err.message;
            statusAlert.classList.remove('alert-warning');
            statusAlert.classList.add('alert-danger');
        }
    }

    async function loadMpInstallments(amount) {
        const select = document.getElementById('mp-installments');
        if (!select) return;

        try {
            const resp = await fetch(
                `${config.mpInstallmentsUrl}?amount=${amount.toFixed(2)}`,
                { headers: { 'X-Requested-With': 'XMLHttpRequest' } }
            );
            const data = await resp.json();
            mpPayerCosts = data.payer_costs || [];
        } catch (_) {
            mpPayerCosts = [];
        }

        renderInstallmentOptions(amount);
    }

    function renderInstallmentOptions(amount) {
        const select = document.getElementById('mp-installments');
        if (!select) return;

        const buyerPaysFee = document.querySelector('input[name="mp-fee-payer"]:checked')?.value === 'true';

        if (mpPayerCosts.length === 0) {
            select.innerHTML = '';
            for (let n = 1; n <= 6; n++) {
                const opt = document.createElement('option');
                opt.value = n;
                opt.text = n === 1 ? `1x de R$ ${amount.toFixed(2)} (sem juros)` : `${n}x de R$ ${(amount / n).toFixed(2)}`;
                select.appendChild(opt);
            }
            return;
        }

        select.innerHTML = '';
        mpPayerCosts.forEach(pc => {
            const n = pc.installments;
            const rate = pc.installment_rate;
            const opt = document.createElement('option');
            opt.value = n;

            if (buyerPaysFee) {
                const total = amount * (1 + rate / 100);
                const perInstall = total / n;
                if (n === 1 || rate === 0) {
                    opt.text = `${n}x de R$ ${(amount / n).toFixed(2)} (sem juros)`;
                } else {
                    opt.text = `${n}x de R$ ${perInstall.toFixed(2)} → total R$ ${total.toFixed(2)} (juros ${rate}%)`;
                }
            } else {
                if (n === 1 || rate === 0) {
                    opt.text = `${n}x de R$ ${(amount / n).toFixed(2)} (sem juros)`;
                } else {
                    opt.text = `${n}x de R$ ${(amount / n).toFixed(2)} (taxa ${rate}% pelo vendedor)`;
                }
            }

            select.appendChild(opt);
        });
    }

    // ---- Mercado Pago: polling de status ----

    function startMpPolling() {
        stopMpPolling();
        mpPollInterval = setInterval(async () => {
            if (!mpOrderId) { stopMpPolling(); return; }
            try {
                const resp = await fetch(`${config.mpOrderStatusUrl}?order_id=${mpOrderId}`, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await resp.json();
                const status = data.status;
                const statusAlert = document.getElementById('payment-status-alert');

                if (status === 'paid' || status === 'processed') {
                    stopMpPolling();
                    if (statusAlert) {
                        statusAlert.innerText = `✓ PAGAMENTO APROVADO! Registrando...`;
                        statusAlert.classList.remove('d-none', 'alert-warning', 'alert-danger');
                        statusAlert.classList.add('alert-success');
                    }
                    await proceedMercadoPagoFlow();
                } else if (['failed', 'canceled', 'expired'].includes(status)) {
                    stopMpPolling();
                    if (statusAlert) {
                        statusAlert.innerText = `✗ Pagamento ${status}. Tente novamente.`;
                        statusAlert.classList.remove('d-none', 'alert-warning', 'alert-success');
                        statusAlert.classList.add('alert-danger');
                    }
                    const btnCancel = document.getElementById('btn-cancel-order');
                    const btnContinue = document.getElementById('btn-mp-continue');
                    const btnSimulate = document.getElementById('btn-mp-simulate');
                    if (btnCancel) btnCancel.disabled = true;
                    if (btnContinue) btnContinue.style.display = 'none';
                    if (btnSimulate) btnSimulate.style.display = 'none';
                    mpOrderId = null; mpMethod = null; mpAmount = 0;
                }
            } catch (_) { /* silencioso durante polling */ }
        }, 4000);
    }

    function stopMpPolling() {
        if (mpPollInterval) {
            clearInterval(mpPollInterval);
            mpPollInterval = null;
        }
    }

    // ---- Mercado Pago: simulação de aprovação (apenas em teste) ----

    async function simulateMpApproval(status = 'processed') {
        if (!mpOrderId) { alert('Nenhuma order ativa para simular.'); return; }

        const statusAlert = document.getElementById('payment-status-alert');
        if (statusAlert) {
            statusAlert.innerText = 'Simulando aprovação...';
            statusAlert.classList.remove('d-none', 'alert-danger', 'alert-success');
            statusAlert.classList.add('alert-warning');
        }

        const formData = new FormData();
        formData.append('order_id', mpOrderId);
        formData.append('status', status);
        formData.append('csrfmiddlewaretoken', getCsrf());

        try {
            const resp = await fetch(config.mpSimulateUrl, {
                method: 'POST', body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            const data = await resp.json();

            if (!resp.ok) {
                throw new Error(data.error || JSON.stringify(data.details) || 'Erro ao simular');
            }
            if (statusAlert) {
                statusAlert.innerText = 'Simulação enviada. Aguardando polling confirmar...';
            }
        } catch (err) {
            if (statusAlert) {
                statusAlert.innerText = 'ERRO na simulação: ' + err.message;
                statusAlert.classList.remove('alert-warning');
                statusAlert.classList.add('alert-danger');
            }
        }
    }

    // Expõe funções chamadas por onclick inline no HTML
    window.confirmPayment = confirmPayment;
    window.goToReceipt = goToReceipt;
    window.finishFlow = finishFlow;
    window.proceedMercadoPagoFlow = proceedMercadoPagoFlow;
    window.cancelMercadoPagoOrder = cancelMercadoPagoOrder;
    window.simulateMpApproval = simulateMpApproval;

})();
