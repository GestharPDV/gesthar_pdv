"""
Carga de dados para testar o sistema de notificações gestacionais.

Uso:
    python manage.py seed_test_data           # cria/atualiza dados
    python manage.py seed_test_data --reset   # apaga tudo e recria
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from customer.models import Customer
from notifications.models import Notification
from notifications.services import run_milestone_check


# ---------------------------------------------------------------------------
# CPFs válidos (verificados pelo algoritmo brasileiro)
# ---------------------------------------------------------------------------
CPFS = [
    "11144477735",
    "52998224725",
    "33344455508",
    "44455566619",
    "55566677720",
    "66677788830",
    "77788899941",
    "01234567890",
]


def _dpp_para_semana(semanas: int) -> date:
    """
    Retorna a DPP (Data Prevista do Parto) que coloca a cliente
    exatamente na semana gestacional indicada HOJE.

    Fórmula inversa de current_weeks:
        current_weeks = (hoje − (DPP − 280)) // 7
    → DPP = hoje + 280 − semanas * 7
    """
    return date.today() + timedelta(days=280 - semanas * 7)


# ---------------------------------------------------------------------------
# Definição dos cenários de teste
# ---------------------------------------------------------------------------
# Cada tupla: (nome, cpf, email, phone, baby_due_date, nota_do_cenário)
def _cenarios():
    hoje = date.today()
    return [
        # -- CASOS NORMAIS --------------------------------------------------
        {
            "name":         "Ana Gestante 28 Semanas",
            "cpf_cnpj":     CPFS[0],
            "email":        "ana.28sem@teste.com",
            "phone":        "86988001001",
            "baby_due_date": _dpp_para_semana(28),
            "_cenario":     "Normal - 28 semanas (sem alerta ainda)",
        },
        {
            "name":         "Beatriz Gestante 35 Semanas",
            "cpf_cnpj":     CPFS[1],
            "email":        "beatriz.35sem@teste.com",
            "phone":        "86988002002",
            "baby_due_date": _dpp_para_semana(35),
            "_cenario":     "Normal - 35 semanas exatas (alerta 35_weeks)",
        },
        {
            "name":         "Carla Gestante 38 Semanas",
            "cpf_cnpj":     CPFS[2],
            "email":        "carla.38sem@teste.com",
            "phone":        "86988003003",
            "baby_due_date": _dpp_para_semana(38),
            "_cenario":     "Normal - 38 semanas (alerta 35_weeks tambem)",
        },
        {
            "name":         "Diana Pos-parto 10 dias",
            "cpf_cnpj":     CPFS[3],
            "email":        "diana.pos@teste.com",
            "phone":        "86988004004",
            "baby_due_date": hoje - timedelta(days=10),
            "_cenario":     "Normal - pos-parto recente (alerta post_partum)",
        },
        # -- EDGE CASES -----------------------------------------------------
        {
            "name":         "Elisa Borda 34 Semanas e 6 Dias",
            "cpf_cnpj":     CPFS[4],
            "email":        "elisa.34s6d@teste.com",
            "phone":        "86988005005",
            # 34 semanas + 6 dias = 244 dias desde concepcao -> DPP = hoje + 36
            "baby_due_date": hoje + timedelta(days=36),
            "_cenario":     "Edge - 34s6d (244 dias = semana 34, NAO dispara alerta)",
        },
        {
            "name":         "Fernanda DPP Exatamente Hoje",
            "cpf_cnpj":     CPFS[5],
            "email":        "fernanda.dpphodie@teste.com",
            "phone":        "86988006006",
            "baby_due_date": hoje,   # DPP = hoje -> 40 semanas, ainda Gestante
            "_cenario":     "Edge - DPP hoje (40 sem, Gestante, alerta 35_weeks; NAO post_partum)",
        },
        {
            "name":         "Giovana Sem Telefone 36 Semanas",
            "cpf_cnpj":     CPFS[6],
            "email":        "giovana.semfone@teste.com",
            "phone":        None,    # Sem WhatsApp
            "baby_due_date": _dpp_para_semana(36),
            "_cenario":     "Edge - sem telefone (alerta gerado, botao WhatsApp NAO aparece)",
        },
        {
            "name":         "Helena Sem DPP",
            "cpf_cnpj":     CPFS[7],
            "email":        "helena.semdpp@teste.com",
            "phone":        "86988008008",
            "baby_due_date": None,   # Cliente normal, sem gestacao
            "_cenario":     "Edge - sem DPP (nenhuma notificacao gerada)",
        },
    ]


# ---------------------------------------------------------------------------
# Comando
# ---------------------------------------------------------------------------
class Command(BaseCommand):
    help = "Cria carga de dados de teste para o sistema de notificações gestacionais."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remove os clientes e notificações de teste antes de recriar.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        cenarios = _cenarios()

        if options["reset"]:
            emails = [c["email"] for c in cenarios]
            deleted_n, _ = Notification.objects.filter(
                customer__email__in=emails
            ).delete()
            deleted_c, _ = Customer.objects.filter(email__in=emails).delete()
            self.stdout.write(
                self.style.WARNING(
                    f"Reset: {deleted_c} cliente(s) e {deleted_n} notificação(ões) removidos."
                )
            )

        # ── 1. Criar / atualizar clientes ───────────────────────────────
        self.stdout.write("\n" + "-" * 60)
        self.stdout.write(self.style.HTTP_INFO("  CLIENTES CRIADOS / ATUALIZADOS"))
        self.stdout.write("-" * 60)

        clientes_criados = []
        for dados in cenarios:
            cenario = dados.pop("_cenario")
            cliente, criado = Customer.objects.update_or_create(
                email=dados["email"],
                defaults=dados,
            )
            clientes_criados.append(cliente)
            acao = "NOVO  " if criado else "ATUAL."
            weeks = cliente.current_weeks
            stage = cliente.gestational_stage or "-"
            dpp_str = str(cliente.baby_due_date) if cliente.baby_due_date else "-"
            weeks_str = ("sem " + str(weeks)) if weeks is not None else "-"
            self.stdout.write(
                f"  [{acao}] {cliente.name:<35} "
                f"DPP: {dpp_str}  "
                f"{stage:<12} "
                f"{weeks_str:>8}"
            )
            self.stdout.write(f"          -> {cenario}")

        # ── 2. Rodar verificação de marcos ──────────────────────────────
        self.stdout.write("\n" + "-" * 60)
        self.stdout.write(self.style.HTTP_INFO("  VERIFICAÇÃO DE MARCOS (run_milestone_check)"))
        self.stdout.write("-" * 60)
        run_milestone_check()

        # ── 3. Relatório de notificações geradas ────────────────────────
        self.stdout.write("\n" + "-" * 60)
        self.stdout.write(self.style.HTTP_INFO("  NOTIFICAÇÕES NO BANCO"))
        self.stdout.write("-" * 60)

        notifs = (
            Notification.objects
            .filter(customer__in=clientes_criados)
            .select_related("user", "customer")
            .order_by("customer__name", "milestone_key")
        )

        if not notifs.exists():
            self.stdout.write(self.style.WARNING("  Nenhuma notificação gerada."))
        else:
            atual_cliente = None
            for n in notifs:
                if n.customer != atual_cliente:
                    atual_cliente = n.customer
                    self.stdout.write(f"\n  ** {n.customer.name}")
                status = "[lida]" if n.is_read else "[nao lida]"
                self.stdout.write(
                    f"     [{n.milestone_key:<12}] {status:<12} -> {n.user.email}"
                )
                self.stdout.write(f"       \"{n.message}\"")

        # -- 4. Resumo final -----------------------------------------------
        total_notifs = notifs.count()
        self.stdout.write("\n" + "-" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"  OK  {len(clientes_criados)} cliente(s)  |  "
                f"{total_notifs} notificacao(oes) gerada(s)"
            )
        )
        self.stdout.write("-" * 60 + "\n")
        self.stdout.write(
            "  Faça login no sistema para ver as notificações no dashboard.\n"
        )
