"""
Serviço de verificação de marcos gestacionais.

Executa uma vez por dia (via cache no signal de login) e cria
notificações para cada usuário ativo quando um marco é atingido.
"""
from datetime import date

from django.contrib.auth import get_user_model

from customer.models import Customer
from .models import Notification

User = get_user_model()

# Definição declarativa dos marcos —
# cada entrada tem: chave única, função de checagem e função de mensagem.
MILESTONES = [
    {
        'key': '35_weeks',
        'check': lambda semanas, hoje, dpp: semanas >= 35 and hoje <= dpp,
        'message': lambda c: (
            f"{c.name} atingiu {c.current_weeks} semanas gestacionais! "
            "Considere oferecer itens de enxoval."
        ),
    },
    {
        'key': 'post_partum',
        'check': lambda semanas, hoje, dpp: hoje > dpp,
        'message': lambda c: (
            f"{c.name} entrou no período pós-parto. "
            "Verifique se precisa de atendimento especial."
        ),
    },
]


def run_milestone_check():
    """
    Verifica todos os clientes com DPP cadastrada e cria notificações
    para marcos atingidos que ainda não foram notificados.

    Idempotente: a constraint unique no banco garante que o mesmo marco
    não gera duplicatas para o mesmo usuário/cliente.
    """
    hoje = date.today()

    clientes = (
        Customer.objects
        .filter(baby_due_date__isnull=False)
        .only('id', 'name', 'baby_due_date', 'phone')
    )
    destinatarios = list(User.objects.filter(is_active=True))

    if not destinatarios:
        return

    for cliente in clientes:
        semanas = cliente.current_weeks
        if semanas is None:
            continue

        dpp = cliente.baby_due_date

        for marco in MILESTONES:
            if not marco['check'](semanas, hoje, dpp):
                continue

            mensagem = marco['message'](cliente)

            for usuario in destinatarios:
                Notification.objects.get_or_create(
                    user=usuario,
                    customer=cliente,
                    milestone_key=marco['key'],
                    defaults={'message': mensagem},
                )
