"""Lançamentos, fluxo de caixa e DRE.

Regras que mantêm os números honestos:
- O fluxo de caixa olha a data de pagamento. O que está pendente aparece como previsto.
- A DRE olha a data de competência e o regime é de competência: a compra de
  insumos vai para o estoque (só caixa) e vira custo quando o insumo é usado
  num produto vendido (CMV). Investimentos, aportes e retiradas também ficam
  fora da DRE.
- Receita bruta, descontos, comissões e CMV vêm direto das vendas.
"""

import calendar
from datetime import date, timedelta

from ..fmt import hoje, limites_mes, mes_deslocado, MESES

# grupo: (rótulo, direção, entra na DRE)
GRUPOS = {
    "venda": ("Vendas", "entrada", False),
    "receita": ("Outras receitas", "entrada", True),
    "deducao": ("Deduções e impostos", "saida", True),
    "custo": ("Custos variáveis de produção", "saida", True),
    "despesa_variavel": ("Despesas variáveis", "saida", True),
    "despesa_fixa": ("Despesas fixas", "saida", True),
    "receita_financeira": ("Receitas financeiras", "entrada", True),
    "despesa_financeira": ("Despesas financeiras", "saida", True),
    "estoque": ("Compras de insumos", "saida", False),
    "investimento": ("Investimentos", "saida", False),
    "aporte": ("Aportes e empréstimos", "entrada", False),
    "retirada": ("Retiradas e amortizações", "saida", False),
}
GRUPOS_EDITAVEIS = [g for g in GRUPOS if g not in ("venda", "estoque")]
SISTEMA = {"venda": "Vendas", "estoque": "Compra de insumos"}

ATIVIDADE = {
    "venda": "operacional", "receita": "operacional", "deducao": "operacional",
    "custo": "operacional", "despesa_variavel": "operacional", "despesa_fixa": "operacional",
    "receita_financeira": "operacional", "despesa_financeira": "operacional", "estoque": "operacional",
    "investimento": "investimento", "aporte": "financiamento", "retirada": "financiamento",
}


def direcao(grupo):
    return GRUPOS[grupo][1]


def categoria_sistema(conn, grupo):
    row = conn.execute("SELECT id FROM categorias WHERE grupo = ? AND sistema = 1", (grupo,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO categorias (nome, grupo, sistema) VALUES (?, ?, 1)", (SISTEMA[grupo], grupo)
    )
    return cur.lastrowid


def categorias_por_grupo(conn, incluir_sistema=False):
    rows = conn.execute("SELECT * FROM categorias ORDER BY nome").fetchall()
    saida = {g: [] for g in GRUPOS}
    for r in rows:
        if r["sistema"] and not incluir_sistema:
            continue
        saida.setdefault(r["grupo"], []).append(r)
    return saida


# ---------------------------------------------------------------- lançamentos

def salvar_lancamento(conn, dados, lancamento_id=None):
    cat = conn.execute("SELECT grupo FROM categorias WHERE id = ?", (dados["categoria_id"],)).fetchone()
    if cat is None:
        raise ValueError("Escolha uma categoria.")
    if dados["valor"] is None or dados["valor"] <= 0:
        raise ValueError("Informe um valor maior que zero.")
    if not dados.get("descricao"):
        raise ValueError("Informe uma descrição.")
    tipo = direcao(cat["grupo"])
    campos = (
        dados["descricao"], dados["valor"], tipo, dados["categoria_id"], dados.get("conta_id"),
        dados["competencia"], dados["vencimento"], dados.get("pagamento"), dados.get("observacao"),
    )
    if lancamento_id:
        conn.execute(
            "UPDATE lancamentos SET descricao=?, valor=?, tipo=?, categoria_id=?, conta_id=?, competencia=?, "
            "vencimento=?, pagamento=?, observacao=? WHERE id = ?",
            (*campos, lancamento_id),
        )
        return lancamento_id
    cur = conn.execute(
        "INSERT INTO lancamentos (descricao, valor, tipo, categoria_id, conta_id, competencia, vencimento, "
        "pagamento, observacao) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        campos,
    )
    return cur.lastrowid


def status_lancamento(l, hoje_iso=None):
    hoje_iso = hoje_iso or hoje().isoformat()
    if l["pagamento"]:
        return "pago"
    if l["vencimento"] < hoje_iso:
        return "atrasado"
    if l["vencimento"] == hoje_iso:
        return "hoje"
    return "pendente"


def pendencias(conn, dias=7):
    """Atrasados e o que vence nos próximos `dias` dias."""
    h = hoje()
    limite = (h + timedelta(days=dias)).isoformat()
    rows = conn.execute(
        "SELECT l.*, c.nome AS categoria, c.grupo FROM lancamentos l JOIN categorias c ON c.id = l.categoria_id "
        "WHERE l.pagamento IS NULL AND l.vencimento <= ? ORDER BY l.vencimento, l.id",
        (limite,),
    ).fetchall()
    resumo = {"pagar": 0, "receber": 0, "atrasado_pagar": 0, "atrasado_receber": 0}
    for r in rows:
        chave = "receber" if r["tipo"] == "entrada" else "pagar"
        resumo[chave] += r["valor"]
        if r["vencimento"] < h.isoformat():
            resumo[f"atrasado_{chave}"] += r["valor"]
    return rows, resumo


def gerar_recorrencias(conn, ano, mes):
    """Cria os lançamentos do mês para cada despesa recorrente ativa. Não duplica."""
    _, ultimo = calendar.monthrange(ano, mes)
    prefixo = f"{ano:04d}-{mes:02d}"
    criados = 0
    for r in conn.execute("SELECT r.*, c.grupo FROM recorrencias r JOIN categorias c ON c.id = r.categoria_id WHERE r.ativa = 1"):
        existe = conn.execute(
            "SELECT 1 FROM lancamentos WHERE origem = 'recorrente' AND origem_id = ? AND substr(competencia, 1, 7) = ?",
            (r["id"], prefixo),
        ).fetchone()
        if existe:
            continue
        dia = date(ano, mes, min(max(r["dia"], 1), ultimo)).isoformat()
        conn.execute(
            "INSERT INTO lancamentos (descricao, valor, tipo, categoria_id, conta_id, competencia, vencimento, origem, origem_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'recorrente', ?)",
            (r["descricao"], r["valor"], direcao(r["grupo"]), r["categoria_id"], r["conta_id"], dia, dia, r["id"]),
        )
        criados += 1
    return criados


# ---------------------------------------------------------------- saldos e fluxo de caixa

def _assinado():
    return "CASE l.tipo WHEN 'entrada' THEN l.valor ELSE -l.valor END"


def saldo_em(conn, data_iso, conta_id=None):
    """Saldo realizado no fim do dia `data_iso`."""
    filtro_conta = " AND l.conta_id = ?" if conta_id else ""
    params = [data_iso] + ([conta_id] if conta_id else [])
    mov = conn.execute(
        f"SELECT COALESCE(SUM({_assinado()}), 0) FROM lancamentos l WHERE l.pagamento IS NOT NULL AND l.pagamento <= ?{filtro_conta}",
        params,
    ).fetchone()[0]
    if conta_id:
        inicial = conn.execute("SELECT saldo_inicial FROM contas WHERE id = ?", (conta_id,)).fetchone()[0]
    else:
        inicial = conn.execute("SELECT COALESCE(SUM(saldo_inicial), 0) FROM contas").fetchone()[0]
    return inicial + mov


def saldos_contas(conn):
    h = hoje().isoformat()
    contas = []
    for c in conn.execute("SELECT * FROM contas WHERE ativa = 1 ORDER BY id"):
        a_receber, a_pagar = conn.execute(
            "SELECT COALESCE(SUM(CASE WHEN tipo='entrada' THEN valor END), 0), "
            "COALESCE(SUM(CASE WHEN tipo='saida' THEN valor END), 0) FROM lancamentos "
            "WHERE pagamento IS NULL AND conta_id = ?",
            (c["id"],),
        ).fetchone()
        contas.append({**dict(c), "saldo": saldo_em(conn, h, c["id"]), "a_receber": a_receber, "a_pagar": a_pagar})
    # lançamentos sem conta entram no total
    sem_conta = conn.execute(
        f"SELECT COALESCE(SUM({_assinado()}), 0) FROM lancamentos l WHERE l.pagamento IS NOT NULL AND l.pagamento <= ? AND l.conta_id IS NULL",
        (h,),
    ).fetchone()[0]
    return contas, sem_conta


def fluxo_diario(conn, inicio, fim):
    """Linha por dia: realizado até hoje, projetado (com pendentes) a partir de hoje."""
    h = hoje()
    ini_iso, fim_iso = inicio.isoformat(), fim.isoformat()
    saldo = saldo_em(conn, (inicio - timedelta(days=1)).isoformat())

    realizados = {}
    for r in conn.execute(
        "SELECT pagamento AS dia, SUM(CASE WHEN tipo='entrada' THEN valor ELSE 0 END) e, "
        "SUM(CASE WHEN tipo='saida' THEN valor ELSE 0 END) s FROM lancamentos "
        "WHERE pagamento BETWEEN ? AND ? GROUP BY pagamento",
        (ini_iso, fim_iso),
    ):
        realizados[r["dia"]] = (r["e"], r["s"])

    previstos = {}
    for r in conn.execute(
        "SELECT vencimento AS dia, SUM(CASE WHEN tipo='entrada' THEN valor ELSE 0 END) e, "
        "SUM(CASE WHEN tipo='saida' THEN valor ELSE 0 END) s FROM lancamentos "
        "WHERE pagamento IS NULL AND vencimento <= ? GROUP BY vencimento",
        (fim_iso,),
    ):
        # atrasados são projetados para hoje (ou para o início, se o período é futuro)
        dia = max(r["dia"], h.isoformat(), ini_iso)
        e, s = previstos.get(dia, (0, 0))
        previstos[dia] = (e + r["e"], s + r["s"])

    dias = []
    projetado = None
    d = inicio
    while d <= fim:
        iso = d.isoformat()
        e, s = realizados.get(iso, (0, 0))
        pe, ps = previstos.get(iso, (0, 0)) if d >= h else (0, 0)
        saldo += e - s
        if d >= h:
            projetado = (saldo if projetado is None else projetado + e - s) + pe - ps
        dias.append({
            "data": iso, "entradas": e, "saidas": s, "prev_entradas": pe, "prev_saidas": ps,
            "saldo": saldo if d <= h else None, "projetado": projetado, "futuro": d > h,
        })
        d += timedelta(days=1)
    return dias


def fluxo_mensal(conn, ano):
    """Caixa realizado por mês e por atividade (operacional, investimento, financiamento)."""
    linhas = {}
    for r in conn.execute(
        "SELECT CAST(substr(l.pagamento, 6, 2) AS INTEGER) mes, c.grupo, "
        f"SUM({_assinado()}) v FROM lancamentos l JOIN categorias c ON c.id = l.categoria_id "
        "WHERE l.pagamento IS NOT NULL AND substr(l.pagamento, 1, 4) = ? GROUP BY mes, c.grupo",
        (f"{ano:04d}",),
    ):
        linhas.setdefault(r["grupo"], [0] * 12)[r["mes"] - 1] += r["v"]

    saldo = saldo_em(conn, f"{ano - 1:04d}-12-31")
    ordem = ["venda", "receita", "receita_financeira", "estoque", "custo", "deducao",
             "despesa_variavel", "despesa_fixa", "despesa_financeira", "investimento", "aporte", "retirada"]
    blocos = []
    for atividade, rotulo in (("operacional", "Atividades operacionais"),
                              ("investimento", "Investimentos"),
                              ("financiamento", "Sócios e financiamentos")):
        itens = [
            {"rotulo": GRUPOS[g][0], "valores": linhas[g], "total": sum(linhas[g])}
            for g in ordem if ATIVIDADE[g] == atividade and g in linhas
        ]
        soma = [sum(i["valores"][m] for i in itens) for m in range(12)]
        blocos.append({"rotulo": rotulo, "itens": itens, "valores": soma, "total": sum(soma)})

    geracao = [sum(b["valores"][m] for b in blocos) for m in range(12)]
    saldos_finais = []
    for m in range(12):
        saldo += geracao[m]
        saldos_finais.append(saldo)
    return {
        "colunas": MESES, "blocos": blocos, "geracao": geracao, "total": sum(geracao),
        "saldo_final": saldos_finais, "saldo_inicial": saldos_finais[0] - geracao[0],
    }


# ---------------------------------------------------------------- DRE

def _linha(chave, rotulo, tipo, n, valores=None):
    valores = valores or [0] * n
    return {"chave": chave, "rotulo": rotulo, "tipo": tipo, "valores": valores, "itens": []}


def dre(conn, meses):
    """DRE gerencial para uma lista de meses [(ano, mes)].

    Valores são assinados pelo efeito no resultado: receitas positivas, custos negativos.
    """
    n = len(meses)
    chaves = [f"{a:04d}-{m:02d}" for a, m in meses]
    idx = {k: i for i, k in enumerate(chaves)}
    ini = limites_mes(*meses[0])[0].isoformat()
    fim = limites_mes(*meses[-1])[1].isoformat()

    vendas = {k: {"bruto": 0, "desconto": 0, "comissao": 0, "cmv": 0, "unidades": 0, "pedidos": 0} for k in chaves}
    for r in conn.execute(
        "SELECT substr(data, 1, 7) m, SUM(bruto) bruto, SUM(desconto) desconto, SUM(comissao) comissao, "
        "SUM(cmv) cmv, SUM(unidades) unidades, COUNT(*) pedidos FROM vendas WHERE data BETWEEN ? AND ? GROUP BY m",
        (ini, fim),
    ):
        if r["m"] in vendas:
            vendas[r["m"]] = dict(r)

    perdas = [0] * n
    for r in conn.execute(
        "SELECT substr(data, 1, 7) m, SUM(-quantidade * custo_unitario) v FROM movimentos "
        "WHERE tipo IN ('perda', 'ajuste_entrada', 'ajuste_saida') AND data BETWEEN ? AND ? GROUP BY m",
        (ini, fim),
    ):
        if r["m"] in idx:
            perdas[idx[r["m"]]] = round(r["v"] or 0)

    por_cat = {}
    for r in conn.execute(
        "SELECT substr(l.competencia, 1, 7) m, c.id, c.nome, c.grupo, "
        f"SUM({_assinado()}) v FROM lancamentos l JOIN categorias c ON c.id = l.categoria_id "
        "WHERE l.competencia BETWEEN ? AND ? GROUP BY m, c.id",
        (ini, fim),
    ):
        if not GRUPOS.get(r["grupo"], (None, None, False))[2] or r["m"] not in idx:
            continue
        chave = (r["grupo"], r["id"], r["nome"])
        por_cat.setdefault(chave, [0] * n)[idx[r["m"]]] += r["v"]

    def grupo(chave, rotulo, extras):
        """extras: [(rótulo, valores)] vindos das vendas; categorias são somadas em seguida."""
        linha = _linha(chave, rotulo, "grupo", n)
        for rot, vals in extras:
            linha["itens"].append({"rotulo": rot, "valores": vals})
        for (g, _cid, nome), vals in sorted(por_cat.items(), key=lambda kv: kv[0][2]):
            if g in chave.split("+"):
                linha["itens"].append({"rotulo": nome, "valores": vals})
        linha["valores"] = [sum(i["valores"][m] for i in linha["itens"]) for m in range(n)]
        linha["itens"] = [i for i in linha["itens"] if any(i["valores"])]
        return linha

    col = lambda campo, sinal=1: [sinal * vendas[k][campo] for k in chaves]

    receita = grupo("receita", "Receita bruta", [("Vendas de produtos", col("bruto"))])
    deducoes = grupo("deducao", "(−) Deduções", [("Descontos concedidos", col("desconto", -1))])
    rl = _linha("receita_liquida", "Receita líquida", "subtotal", n,
                [receita["valores"][m] + deducoes["valores"][m] for m in range(n)])
    cmv = grupo("custo", "(−) Custo dos produtos vendidos", [
        ("Insumos e embalagens dos produtos vendidos", col("cmv", -1)),
        ("Perdas e ajustes de estoque", [-p for p in perdas]),
    ])
    lb = _linha("lucro_bruto", "Lucro bruto", "subtotal", n,
                [rl["valores"][m] + cmv["valores"][m] for m in range(n)])
    dv = grupo("despesa_variavel", "(−) Despesas variáveis", [("Comissões e taxas dos canais", col("comissao", -1))])
    mc = _linha("margem_contribuicao", "Margem de contribuição", "subtotal", n,
                [lb["valores"][m] + dv["valores"][m] for m in range(n)])
    df = grupo("despesa_fixa", "(−) Despesas fixas", [])
    ro = _linha("resultado_operacional", "Resultado operacional", "subtotal", n,
                [mc["valores"][m] + df["valores"][m] for m in range(n)])
    fin = grupo("receita_financeira+despesa_financeira", "(±) Resultado financeiro", [])
    ll = _linha("lucro_liquido", "Lucro líquido", "resultado", n,
                [ro["valores"][m] + fin["valores"][m] for m in range(n)])

    linhas = [receita, deducoes, rl, cmv, lb, dv, mc, df, ro, fin, ll]
    for l in linhas:
        l["total"] = sum(l["valores"])
        for i in l["itens"]:
            i["total"] = sum(i["valores"])

    def indicadores(m):
        if m is None:
            rb = receita["total"]; mcv = mc["total"]; fixas = -df["total"]; lucro = ll["total"]
            unidades = sum(v["unidades"] for v in vendas.values()); pedidos = sum(v["pedidos"] for v in vendas.values())
            dias = sum(calendar.monthrange(a, mm)[1] for a, mm in meses)
        else:
            rb = receita["valores"][m]; mcv = mc["valores"][m]; fixas = -df["valores"][m]; lucro = ll["valores"][m]
            v = vendas[chaves[m]]; unidades = v["unidades"]; pedidos = v["pedidos"]
            dias = calendar.monthrange(*meses[m])[1]
        mc_pct = mcv / rb if rb else None
        mc_unidade = mcv / unidades if unidades else None
        pe_receita = fixas / mc_pct if mc_pct and mc_pct > 0 else None
        pe_unidades = fixas / mc_unidade if mc_unidade and mc_unidade > 0 else None
        return {
            "receita": rb, "pedidos": pedidos, "unidades": unidades,
            "ticket_medio": rb / pedidos if pedidos else None,
            "margem_bruta": lb["valores"][m] / rb if m is not None and rb else (lb["total"] / rb if rb else None),
            "margem_contribuicao": mc_pct,
            "margem_liquida": lucro / rb if rb else None,
            "despesas_fixas": fixas,
            "ponto_equilibrio": pe_receita,
            "pe_unidades": pe_unidades,
            "pe_unidades_dia": pe_unidades / dias if pe_unidades else None,
            "unidades_dia": unidades / dias if dias else 0,
            "dias": dias,
        }

    return {
        "colunas": [MESES[m - 1] for _, m in meses],
        "chaves": chaves,
        "linhas": linhas,
        "por_mes": [indicadores(m) for m in range(n)],
        "acumulado": indicadores(None),
        "linha": {l["chave"]: l for l in linhas},
    }


def dre_ano(conn, ano):
    return dre(conn, [(ano, m) for m in range(1, 13)])


def dre_mes(conn, ano, mes):
    return dre(conn, [(ano, mes)])


def ultimos_meses(ano, mes, n):
    return [mes_deslocado(ano, mes, -i) for i in range(n - 1, -1, -1)]
