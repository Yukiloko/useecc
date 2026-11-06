import json

from flask import Blueprint, redirect, render_template, request, url_for

from ..db import get_db
from ..fmt import hoje, limites_mes, ler_dinheiro, ler_numero
from ..services import vendas as sv
from ..services import estoque
from ._util import ErroFormulario, campo, data, dinheiro, erro, inteiro, ok, periodo_mes

bp = Blueprint("vendas", __name__, url_prefix="/vendas")


@bp.route("/")
def lista():
    conn = get_db()
    per = periodo_mes()
    ini, fim = (d.isoformat() for d in limites_mes(per["ano"], per["mes"]))
    canal_id = request.args.get("canal", type=int)
    filtro = " AND v.canal_id = ?" if canal_id else ""
    params = [ini, fim] + ([canal_id] if canal_id else [])
    rows = conn.execute(
        "SELECT v.*, c.nome AS canal, l.pagamento AS recebido_em, l.vencimento AS receber_em "
        "FROM vendas v JOIN canais c ON c.id = v.canal_id "
        "LEFT JOIN lancamentos l ON l.origem = 'venda' AND l.origem_id = v.id "
        f"WHERE v.data BETWEEN ? AND ?{filtro} ORDER BY v.data DESC, v.id DESC",
        params,
    ).fetchall()
    nomes = {r["id"]: r["nome"] for r in conn.execute("SELECT id, nome FROM produtos")}
    itens = {}
    for it in conn.execute(
        "SELECT vi.* FROM venda_itens vi JOIN vendas v ON v.id = vi.venda_id WHERE v.data BETWEEN ? AND ?", (ini, fim)
    ):
        texto = f"{ler_qtd(it['quantidade'])}× {nomes.get(it['produto_id'], '?')}"
        if it["sabores"]:
            texto += " (" + ", ".join(nomes.get(int(s), "?") for s in it["sabores"].split(",")) + ")"
        itens.setdefault(it["venda_id"], []).append(texto)
    tot = {
        "pedidos": len(rows),
        "bruto": sum(r["bruto"] for r in rows),
        "desconto": sum(r["desconto"] for r in rows),
        "comissao": sum(r["comissao"] for r in rows),
        "cmv": sum(r["cmv"] for r in rows),
        "unidades": sum(r["unidades"] for r in rows),
    }
    tot["liquido"] = tot["bruto"] - tot["desconto"] - tot["comissao"]
    tot["margem"] = tot["liquido"] - tot["cmv"]
    canais = conn.execute("SELECT * FROM canais ORDER BY nome").fetchall()
    ranking = sv.ranking_produtos(conn, ini, fim)
    return render_template("vendas/lista.html", per=per, vendas=rows, itens=itens, tot=tot,
                           canais=canais, canal_id=canal_id, ranking=ranking)


def ler_qtd(q):
    return int(q) if float(q).is_integer() else q


def _contexto_form(conn):
    produtos = conn.execute("SELECT * FROM produtos WHERE ativo = 1 ORDER BY sabores_por_kit, nome").fetchall()
    canais = conn.execute("SELECT * FROM canais WHERE ativo = 1 ORDER BY id").fetchall()
    dados = {
        "produtos": [
            {"id": p["id"], "nome": p["nome"], "preco": p["preco"], "kit": p["sabores_por_kit"],
             "estoque": p["estoque"], "custo": round(estoque.custo_unitario_produto(conn, p["id"]))}
            for p in produtos
        ],
        "canais": [
            {"id": c["id"], "nome": c["nome"], "pct": c["comissao_pct"] + c["taxa_pagamento_pct"],
             "fixa": c["taxa_fixa"], "prazo": c["prazo_dias"]}
            for c in canais
        ],
    }
    return {"produtos": produtos, "canais": canais, "dados_json": json.dumps(dados)}


@bp.route("/nova", methods=["GET", "POST"])
def nova():
    conn = get_db()
    if request.method == "POST":
        try:
            itens = _ler_itens()
            com_txt = request.form.get("comissao", "").strip()
            comissao = ler_dinheiro(com_txt) if com_txt and request.form.get("comissao_manual") == "1" else None
            sv.registrar_venda(
                conn, data("data"), inteiro("canal_id"), itens,
                desconto=dinheiro("desconto", 0), comissao=comissao,
                cliente=campo("cliente"), observacao=campo("observacao"),
                recebido=None if request.form.get("recebido") is None else request.form.get("recebido") == "1",
            )
            conn.commit()
            ok("Venda registrada.")
            if request.form.get("continuar"):
                return redirect(url_for("vendas.nova", canal=inteiro("canal_id"), data=request.form.get("data")))
            return redirect(url_for("vendas.lista", mes=request.form.get("data", "")[:7]))
        except (ErroFormulario, ValueError) as e:
            conn.rollback()
            erro(e)
    ctx = _contexto_form(conn)
    return render_template("vendas/form.html", **ctx,
                           data_padrao=request.args.get("data") or hoje().isoformat(),
                           canal_padrao=request.args.get("canal", type=int))


def _ler_itens():
    produtos = request.form.getlist("item_produto")
    qtds = request.form.getlist("item_qtd")
    precos = request.form.getlist("item_preco")
    sabores = request.form.getlist("item_sabores")
    itens = []
    for i, pid in enumerate(produtos):
        if not pid:
            continue
        try:
            q = ler_numero(qtds[i] if i < len(qtds) else "1", 1)
            preco = ler_dinheiro(precos[i]) if i < len(precos) and precos[i].strip() else None
        except ValueError:
            raise ErroFormulario("Quantidade ou preço inválido nos itens.")
        sab = [int(s) for s in (sabores[i] if i < len(sabores) else "").split(",") if s.strip().isdigit()]
        itens.append({"produto_id": int(pid), "quantidade": q, "preco_unitario": preco, "sabores": sab})
    return itens


@bp.route("/<int:venda_id>/excluir", methods=["POST"])
def excluir(venda_id):
    conn = get_db()
    v = conn.execute("SELECT data FROM vendas WHERE id = ?", (venda_id,)).fetchone()
    sv.excluir_venda(conn, venda_id)
    conn.commit()
    ok("Venda excluída. Estoque e caixa foram estornados.")
    return redirect(url_for("vendas.lista", mes=v["data"][:7] if v else None))
