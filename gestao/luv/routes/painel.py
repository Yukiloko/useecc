from datetime import timedelta

from flask import Blueprint, render_template

from .. import charts
from ..db import get_db
from ..fmt import MESES, data_curta, hoje, limites_mes, mes_deslocado
from ..services import estoque, financeiro, vendas
from ._util import periodo_mes

bp = Blueprint("painel", __name__)


def variacao(atual, anterior):
    if not anterior:
        return None
    return (atual - anterior) / abs(anterior)


@bp.route("/")
def index():
    conn = get_db()
    per = periodo_mes()
    ano, mes = per["ano"], per["mes"]
    meses = financeiro.ultimos_meses(ano, mes, 6)
    d6 = financeiro.dre(conn, meses)
    atual, anterior = d6["por_mes"][-1], d6["por_mes"][-2]
    linha = d6["linha"]
    lucro = linha["lucro_liquido"]["valores"]

    contas, sem_conta = financeiro.saldos_contas(conn)
    saldo_total = sum(c["saldo"] for c in contas) + sem_conta
    pend, resumo_pend = financeiro.pendencias(conn, dias=7)
    # repasses de venda são muitos e pequenos: aparecem somados numa linha só
    repasses = [l for l in pend if l["origem"] == "venda"]
    pend = [l for l in pend if l["origem"] != "venda"]
    resumo_repasses = {
        "n": len(repasses), "valor": sum(l["valor"] for l in repasses),
        "primeiro": min((l["vencimento"] for l in repasses), default=None),
        "atrasado": any(l["vencimento"] < hoje().isoformat() for l in repasses),
    }

    ini, fim = limites_mes(ano, mes)
    canais = vendas.resumo_canais(conn, ini.isoformat(), fim.isoformat())
    max_canal = max([c["bruto"] for c in canais] + [1])

    alertas = estoque.lista_de_compras(conn)
    zerados = conn.execute(
        "SELECT nome FROM produtos WHERE ativo = 1 AND sabores_por_kit = 0 AND estoque <= 0 ORDER BY nome"
    ).fetchall()

    grafico_resultado = charts.barras(
        [MESES[m - 1] for _, m in meses],
        [("Receita", linha["receita"]["valores"], "s-receita"),
         ("Lucro líquido", lucro, "s-lucro")],
        altura=220,
    )

    h = hoje()
    fluxo = financeiro.fluxo_diario(conn, h, h + timedelta(days=30))
    grafico_caixa = charts.linhas(
        [data_curta(d["data"]) for d in fluxo],
        [("Saldo previsto", [d["projetado"] for d in fluxo], "s-saldo area")],
        altura=200, mostrar_cada=6,
    )
    saldo_30 = fluxo[-1]["projetado"] if fluxo else saldo_total

    return render_template(
        "painel.html", per=per, atual=atual, anterior=anterior,
        receita=linha["receita"]["valores"][-1], receita_ant=linha["receita"]["valores"][-2],
        lucro=lucro[-1], lucro_ant=lucro[-2], variacao=variacao,
        contas=contas, saldo_total=saldo_total, saldo_30=saldo_30,
        pend=pend, resumo_pend=resumo_pend, repasses=resumo_repasses, canais=canais, max_canal=max_canal,
        alertas=alertas, zerados=zerados,
        grafico_resultado=grafico_resultado, grafico_caixa=grafico_caixa,
        status=financeiro.status_lancamento,
    )
