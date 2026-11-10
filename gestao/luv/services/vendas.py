"""Registro de vendas: baixa o estoque, calcula o CMV e gera o recebimento no caixa."""

from ..fmt import hoje, somar_dias
from . import estoque
from .financeiro import categoria_sistema


def comissao_padrao(canal, base):
    """Comissão do canal sobre o valor do pedido já com desconto."""
    if canal is None or base <= 0:
        return 0
    pct = (canal["comissao_pct"] or 0) + (canal["taxa_pagamento_pct"] or 0)
    return round(base * pct / 100 + (canal["taxa_fixa"] or 0))


def registrar_venda(conn, data, canal_id, itens, desconto=0, comissao=None, cliente=None,
                    observacao=None, recebido=None, baixar_estoque=True):
    """itens: [{"produto_id", "quantidade", "preco_unitario" (centavos, opcional), "sabores": [produto_id]}]

    Kits (sabores_por_kit > 0) precisam da lista de sabores: um id por brownie do kit.
    baixar_estoque=False: venda de antes do controle de estoque. Entra na receita, no CMV
    (pelo custo da ficha) e no caixa, mas não mexe no estoque, que já foi contado.
    """
    if not baixar_estoque and not observacao:
        observacao = "Venda anterior ao controle de estoque"
    canal = conn.execute("SELECT * FROM canais WHERE id = ?", (canal_id,)).fetchone()
    if canal is None:
        raise ValueError("Escolha o canal da venda.")
    linhas = []
    for it in itens:
        if not it.get("produto_id") or not it.get("quantidade") or it["quantidade"] <= 0:
            continue
        p = conn.execute("SELECT * FROM produtos WHERE id = ?", (it["produto_id"],)).fetchone()
        if p is None:
            raise ValueError("Produto não encontrado.")
        preco = it.get("preco_unitario")
        if preco is None:
            preco = p["preco"]
        sabores = [s for s in (it.get("sabores") or []) if s]
        if p["sabores_por_kit"]:
            if len(sabores) != p["sabores_por_kit"]:
                raise ValueError(f"Escolha os {p['sabores_por_kit']} sabores de {p['nome']}.")
            for s in sabores:
                sp = conn.execute("SELECT sabores_por_kit FROM produtos WHERE id = ?", (s,)).fetchone()
                if sp is None or sp["sabores_por_kit"]:
                    raise ValueError("Sabor inválido no kit.")
        linhas.append((p, it["quantidade"], preco, sabores))
    if not linhas:
        raise ValueError("Adicione ao menos um produto.")

    bruto = round(sum(q * preco for _, q, preco, _ in linhas))
    desconto = max(0, min(desconto or 0, bruto))
    if comissao is None:
        comissao = comissao_padrao(canal, bruto - desconto)
    comissao = max(0, comissao)

    cur = conn.execute(
        "INSERT INTO vendas (data, canal_id, cliente, bruto, desconto, comissao, observacao) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (data, canal_id, cliente, bruto, desconto, comissao, observacao),
    )
    venda_id = cur.lastrowid
    cmv = 0.0
    unidades = 0.0
    afetados = set()
    for p, q, preco, sabores in linhas:
        if p["sabores_por_kit"]:
            custo_kit = 0.0
            for linha in estoque.ficha(conn, p["id"]):
                if baixar_estoque:
                    c = estoque.movimentar(conn, data, "insumo", linha.insumo_id, "venda", -linha.quantidade * q,
                                           None, "venda", venda_id)
                    afetados.add(("insumo", linha.insumo_id))
                else:
                    c = linha.custo_unitario
                custo_kit += c * linha.quantidade
            for s in sabores:
                c = estoque.custo_unitario_produto(conn, s)
                if baixar_estoque:
                    estoque.movimentar(conn, data, "produto", s, "venda", -q, c, "venda", venda_id)
                    afetados.add(("produto", s))
                custo_kit += c
            custo_unit = custo_kit
            unidades += q * len(sabores)
        else:
            custo_unit = estoque.custo_unitario_produto(conn, p["id"])
            if baixar_estoque:
                estoque.movimentar(conn, data, "produto", p["id"], "venda", -q, custo_unit, "venda", venda_id)
                afetados.add(("produto", p["id"]))
            unidades += q
        cmv += custo_unit * q
        conn.execute(
            "INSERT INTO venda_itens (venda_id, produto_id, quantidade, preco_unitario, custo_unitario, sabores) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (venda_id, p["id"], q, preco, custo_unit, ",".join(str(s) for s in sabores) or None),
        )
    for item, item_id in afetados:
        estoque.recalcular(conn, item, item_id)
    conn.execute("UPDATE vendas SET cmv = ?, unidades = ? WHERE id = ?", (round(cmv), unidades, venda_id))

    liquido = max(0, bruto - desconto - comissao)
    vencimento = somar_dias(data, canal["prazo_dias"] or 0)
    if recebido is None:
        recebido = vencimento <= hoje().isoformat() and not canal["prazo_dias"]
    if liquido > 0:
        conn.execute(
            "INSERT INTO lancamentos (descricao, valor, tipo, categoria_id, conta_id, competencia, vencimento, "
            "pagamento, origem, origem_id) VALUES (?, ?, 'entrada', ?, ?, ?, ?, ?, 'venda', ?)",
            (f"Venda #{venda_id} · {canal['nome']}{f' · {cliente}' if cliente else ''}", liquido,
             categoria_sistema(conn, "venda"), canal["conta_id"], data, vencimento,
             (vencimento if vencimento <= hoje().isoformat() else data) if recebido else None, venda_id),
        )
    return venda_id


def excluir_venda(conn, venda_id):
    estoque.desfazer_origem(conn, "venda", venda_id)
    conn.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))


def resumo_canais(conn, inicio, fim):
    return conn.execute(
        "SELECT c.id, c.nome, COUNT(v.id) pedidos, COALESCE(SUM(v.bruto), 0) bruto, "
        "COALESCE(SUM(v.desconto), 0) desconto, COALESCE(SUM(v.comissao), 0) comissao, "
        "COALESCE(SUM(v.cmv), 0) cmv, COALESCE(SUM(v.unidades), 0) unidades "
        "FROM canais c LEFT JOIN vendas v ON v.canal_id = c.id AND v.data BETWEEN ? AND ? "
        "GROUP BY c.id HAVING c.ativo = 1 OR COUNT(v.id) > 0 ORDER BY bruto DESC",
        (inicio, fim),
    ).fetchall()


def ranking_produtos(conn, inicio, fim):
    """Produtos vendidos no período. Sabores dentro de kits contam como unidades do sabor."""
    rows = conn.execute(
        "SELECT p.id, p.nome, p.sabores_por_kit, vi.quantidade, vi.preco_unitario, vi.custo_unitario, vi.sabores "
        "FROM venda_itens vi JOIN vendas v ON v.id = vi.venda_id JOIN produtos p ON p.id = vi.produto_id "
        "WHERE v.data BETWEEN ? AND ?",
        (inicio, fim),
    ).fetchall()
    nomes = {r["id"]: r["nome"] for r in conn.execute("SELECT id, nome FROM produtos")}
    agg = {}
    for r in rows:
        a = agg.setdefault(r["id"], {"nome": r["nome"], "quantidade": 0, "receita": 0, "custo": 0, "em_kits": 0})
        a["quantidade"] += r["quantidade"]
        a["receita"] += r["quantidade"] * r["preco_unitario"]
        a["custo"] += r["quantidade"] * r["custo_unitario"]
        if r["sabores"]:
            for s in r["sabores"].split(","):
                sid = int(s)
                b = agg.setdefault(sid, {"nome": nomes.get(sid, "?"), "quantidade": 0, "receita": 0, "custo": 0, "em_kits": 0})
                b["em_kits"] += r["quantidade"]
    lista = sorted(agg.values(), key=lambda a: a["receita"], reverse=True)
    for a in lista:
        a["margem"] = (a["receita"] - a["custo"]) / a["receita"] if a["receita"] else None
    return lista
