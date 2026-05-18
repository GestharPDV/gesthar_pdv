(function () {
    'use strict';

    const config = document.getElementById('pdv-config').dataset;

    function getCsrf() {
        return config.csrfToken;
    }

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
                document.querySelectorAll('.btn-payment-option').forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                const valorRestanteStr = document.getElementById('modal-remaining-balance').innerText.replace('R$', '').replace(',', '.').trim();
                const valorCalculado = parseFloat(valorRestanteStr).toFixed(2);

                if (method === 'PIX') {
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

    // Expõe funções chamadas por onclick inline no HTML
    window.confirmPayment = confirmPayment;
    window.goToReceipt = goToReceipt;
    window.finishFlow = finishFlow;

})();
