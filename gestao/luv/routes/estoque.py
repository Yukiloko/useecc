import json

from flask import Blueprint, redirect, render_template, request, url_for

from ..db import get_db
from ..fmt import hoje, ler_dinheiro, ler_numero
from ..services import estoque as se
from ..services import financeiro as sf
from ._util import ErroFormulario, campo, data, dinheiro, erro, inteiro, numero, ok

bp = Blueprint("estoque", __name__)

CATEGORIAS_INSUMO = {"ingrediente": "Ingredientes", "embalagem": "Embalagens", "outro": "Outros"}


# ---------------------------------------------------------------- insumos

@bp.route("/estoque")
def insumos():
    conn = get_db()
    filtro = request.args.get("filtro", "")
    rows = conn.execute(
        "SELECT * FROM insumos WHERE ativo = 1 ORDER BY CASE categoria WHEN 'ingrediente' THEN 0 WHEN 'embalagem' THEN 1 ELSE 2 END, nome"
    ).fetchall()
    lista = []
    for r in rows:
        st = se.status_insumo(r)
        if filtro == "alerta" and st == "ok":
            continue
        lista.append({**dict(r), "status": st, "valor": max(r["estoque"], 0) * r["custo_medio"]})
    grupos = {}
    for r in lista:
        grupos.setdefault(r["categoria"], []).append(r)
    todos = [{**dict(r), "status": se.status_insumo(r)} for r in rows]
    resumo = {
        "valor": sum(max(r["estoque"], 0) * r["custo_medio"] for r in rows),
        "itens": len(rows),
        "alerta": sum(1 for r in todos if r["status"] != "ok"),
    }
    produtos = conn.execute(
        "SELECT * FROM produtos WHERE ativo = 1 AND sabores_por_kit = 0 ORDER BY nome"
    ).fetchall()
    resumo["valor_produtos"] = sum(max(p["estoque"], 0) * p["custo_medio"] for p in produtos)
    inativos = conn.execute("SELECT COUNT(*) FROM insumos WHERE ativo = 0").fetchone()[0]
    return render_template(
        "estoque/insumos.html", grupos=grupos, nomes_cat=CATEGORIAS_INSUMO, resumo=resumo,
        filtro=filtro, compras=se.lista_de_compras(conn), produtos=produtos, inativos=inativos,
    )


@bp.route("/estoque/insumos/novo", methods=["GET", "POST"])
@bp.route("/estoque/insumos/<int:iid>", methods=["GET", "POST"])
def insumo_form(iid=None):
    conn = get_db()
    ins = conn.execute("SELECT * FROM insumos WHERE id = ?", (iid,)).fetchone() if iid else None
    if request.method == "POST":
        try:
            nome = campo("nome")
            if not nome:
                raise ErroFormulario("Dê um nome ao insumo.")
            unidade = request.form.get("unidade", "g")
            if unidade not in ("g", "ml", "un"):
                unidade = "g"
            categoria = request.form.get("categoria", "ingrediente")
            minimo = numero("estoque_minimo", 0)
            fornecedor = campo("fornecedor")
            if ins:
                conn.execute(
                    "UPDATE insumos SET nome=?, categoria=?, unidade=?, estoque_minimo=?, fornecedor=?, ativo=? WHERE id=?",
                    (nome, categoria, unidade, minimo, fornecedor, 0 if request.form.get("inativo") else 1, iid),
                )
                tem_mov = conn.execute("SELECT 1 FROM movimentos WHERE item='insumo' AND item_id=?", (iid,)).fetchone()
                custo = _custo_informado(unidade)
                if custo is not None and not tem_mov:
                    conn.execute("UPDATE insumos SET custo_medio = ? WHERE id = ?", (custo, iid))
            else:
                custo = _custo_informado(unidade) or 0
                iid = conn.execute(
                    "INSERT INTO insumos (nome, categoria, unidade, estoque_minimo, fornecedor, custo_medio) VALUES (?, ?, ?, ?, ?, ?)",
                    (nome, categoria, unidade, minimo, fornecedor, custo),
                ).lastrowid
                inicial = numero("estoque_inicial", 0)
                if inicial and inicial > 0:
                    se.movimentar(conn, data("data_inicial", hoje().isoformat()), "insumo", iid, "ajuste_entrada",
                                  inicial, custo, "ajuste", None, "Estoque inicial")
                    se.recalcular(conn, "insumo", iid)
            conn.commit()
            ok("Insumo salvo.")
            return redirect(url_for("estoque.insumos"))
        except ErroFormulario as e:
            conn.rollback()
            erro(e)
    movs = []
    if ins:
        movs = conn.execute(
            "SELECT * FROM movimentos WHERE item = 'insumo' AND item_id = ? ORDER BY data DESC, id DESC LIMIT 60", (iid,)
        ).fetchall()
    usos = conn.execute(
        "SELECT p.nome, f.quantidade FROM ficha_tecnica f JOIN produtos p ON p.id = f.produto_id WHERE f.insumo_id = ?",
        (iid,),
    ).fetchall() if ins else []
    return render_template("estoque/insumo_form.html", ins=ins, movs=movs, usos=usos,
                           nomes_cat=CATEGORIAS_INSUMO, rotulos=se.ROTULOS_MOV)


def _custo_informado(unidade):
    """O formulário pede R$/kg, R$/L ou R$/un; guardamos centavos por unidade-base."""
    v = dinheiro("custo", None)
    if v is None:
        return None
    return v / 1000 if unidade in ("g", "ml") else float(v)


@bp.route("/estoque/<item>/<int:item_id>/ajustar", methods=["POST"])
def ajustar(item, item_id):
    conn = get_db()
    try:
        se.ajustar(conn, data("data", hoje().isoformat()), item, item_id, request.form.get("tipo", "perda"),
                   numero("quantidade", obrigatorio=True), campo("observacao"))
        conn.commit()
        ok("Estoque ajustado.")
    except (ErroFormulario, ValueError) as e:
        conn.rollback()
        erro(e)
    return redirect(request.referrer or url_for("estoque.insumos"))


@bp.route("/estoque/movimentos")
def movimentos():
    conn = get_db()
    tipo = request.args.get("tipo", "")
    where, params = "", []
    if tipo:
        where, params = "WHERE m.tipo = ?", [tipo]
    rows = conn.execute(
        "SELECT m.*, COALESCE(i.nome, p.nome) AS nome, i.unidade FROM movimentos m "
        "LEFT JOIN insumos i ON m.item = 'insumo' AND i.id = m.item_id "
        "LEFT JOIN produtos p ON m.item = 'produto' AND p.id = m.item_id "
        f"{where} ORDER BY m.data DESC, m.id DESC LIMIT 300",
        params,
    ).fetchall()
    return render_template("estoque/movimentos.html", movs=rows, rotulos=se.ROTULOS_MOV, tipo=tipo)


# ---------------------------------------------------------------- compras

@bp.route("/compras")
def compras():
    conn = get_db()
    rows = conn.execute(
        "SELECT c.*, l.pagamento, l.vencimento, (SELECT COUNT(*) FROM compra_itens WHERE compra_id = c.id) AS n_itens "
        "FROM compras c LEFT JOIN lancamentos l ON l.origem = 'compra' AND l.origem_id = c.id "
        "ORDER BY c.data DESC, c.id DESC LIMIT 200"
    ).fetchall()
    itens = {}
    for it in conn.execute(
        "SELECT ci.*, i.nome, i.unidade FROM compra_itens ci JOIN insumos i ON i.id = ci.insumo_id"
    ):
        itens.setdefault(it["compra_id"], []).append(it)
    return render_template("estoque/compras.html", compras=rows, itens=itens)


@bp.route("/compras/nova", methods=["GET", "POST"])
def compra_nova():
    conn = get_db()
    if request.method == "POST":
        try:
            ids = request.form.getlist("item_insumo")
            qtds = request.form.getlist("item_qtd")
            valores = request.form.getlist("item_valor")
            itens = []
            for i, iid in enumerate(ids):
                if not iid:
                    continue
                try:
                    q = ler_numero(qtds[i])
                    v = ler_dinheiro(valores[i])
                except (ValueError, IndexError):
                    raise ErroFormulario("Confira quantidade e valor dos itens.")
                if not q or q <= 0 or v is None or v < 0:
                    raise ErroFormulario("Cada item precisa de quantidade e valor.")
                itens.append((int(iid), q, v))
            d = data("data")
            pago = request.form.get("pago") == "1"
            se.registrar_compra(conn, d, itens, fornecedor=campo("fornecedor"), conta_id=inteiro("conta_id"),
                                vencimento=data("vencimento", d, obrigatorio=False) or d, pago=pago,
                                observacao=campo("observacao"))
            conn.commit()
            ok("Compra registrada. Estoque e custo médio atualizados.")
            return redirect(url_for("estoque.compras"))
        except (ErroFormulario, ValueError) as e:
            conn.rollback()
            erro(e)
    insumos = conn.execute("SELECT * FROM insumos WHERE ativo = 1 ORDER BY nome").fetchall()
    sugestao = {}
    if request.args.get("sugestao"):
        sugestao = {c["id"]: c for c in se.lista_de_compras(conn)}
    dados = [{"id": i["id"], "nome": i["nome"], "unidade": i["unidade"], "custo": i["custo_medio"]} for i in insumos]
    fornecedores = [r[0] for r in conn.execute(
        "SELECT DISTINCT fornecedor FROM compras WHERE fornecedor IS NOT NULL AND fornecedor != '' "
        "UNION SELECT DISTINCT fornecedor FROM insumos WHERE fornecedor IS NOT NULL AND fornecedor != ''")]
    return render_template(
        "estoque/compra_form.html", insumos=insumos, dados_json=json.dumps(dados), sugestao=list(sugestao.values()),
        contas=conn.execute("SELECT * FROM contas WHERE ativa = 1").fetchall(), fornecedores=fornecedores,
    )


@bp.route("/compras/<int:cid>/excluir", methods=["POST"])
def compra_excluir(cid):
    conn = get_db()
    se.excluir_compra(conn, cid)
    conn.commit()
    ok("Compra excluída. Estoque e caixa estornados.")
    return redirect(url_for("estoque.compras"))


# ---------------------------------------------------------------- produção

@bp.route("/producao", methods=["GET", "POST"])
def producao():
    conn = get_db()
    faltas = None
    form = {}
    if request.method == "POST":
        form = request.form
        try:
            se.registrar_producao(conn, data("data"), inteiro("produto_id"), numero("lotes", obrigatorio=True),
                                  campo("observacao"), forcar=request.form.get("forcar") == "1")
            conn.commit()
            ok("Produção registrada. Insumos baixados e produtos no estoque.")
            return redirect(url_for("estoque.producao"))
        except se.EstoqueInsuficiente as e:
            conn.rollback()
            faltas = e.faltas
        except (ErroFormulario, ValueError) as e:
            conn.rollback()
            erro(e)
    produtos = conn.execute("SELECT * FROM produtos WHERE ativo = 1 AND sabores_por_kit = 0 ORDER BY nome").fetchall()
    fichas = {}
    for p in produtos:
        fichas[p["id"]] = {
            "rendimento": p["rendimento"],
            "itens": [{"nome": l.nome, "unidade": l.unidade, "qtd": l.quantidade, "custo": l.custo_unitario,
                       "estoque": conn.execute("SELECT estoque FROM insumos WHERE id = ?", (l.insumo_id,)).fetchone()[0]}
                      for l in se.ficha(conn, p["id"])],
        }
    historico = conn.execute(
        "SELECT pr.*, p.nome FROM producoes pr JOIN produtos p ON p.id = pr.produto_id ORDER BY pr.data DESC, pr.id DESC LIMIT 100"
    ).fetchall()
    return render_template("estoque/producao.html", produtos=produtos, fichas_json=json.dumps(fichas),
                           historico=historico, faltas=faltas, form=form)


@bp.route("/producao/<int:pid>/excluir", methods=["POST"])
def producao_excluir(pid):
    conn = get_db()
    se.excluir_producao(conn, pid)
    conn.commit()
    ok("Produção excluída. Insumos devolvidos ao estoque.")
    return redirect(url_for("estoque.producao"))


# ---------------------------------------------------------------- produtos e fichas técnicas

@bp.route("/produtos")
def produtos():
    conn = get_db()
    canais = conn.execute("SELECT * FROM canais WHERE ativo = 1 ORDER BY id").fetchall()
    lista = []
    for p in conn.execute("SELECT * FROM produtos ORDER BY ativo DESC, sabores_por_kit, nome"):
        custo = se.custo_unitario_produto(conn, p["id"])
        teorico = se.custo_teorico(conn, p["id"])
        tem_ficha = conn.execute("SELECT 1 FROM ficha_tecnica WHERE produto_id = ?", (p["id"],)).fetchone() is not None
        margens = []
        for c in canais:
            taxa = p["preco"] * (c["comissao_pct"] + c["taxa_pagamento_pct"]) / 100 + c["taxa_fixa"]
            lucro = p["preco"] - taxa - custo
            margens.append({"canal": c["nome"], "lucro": lucro, "pct": lucro / p["preco"] if p["preco"] else None})
        lista.append({**dict(p), "custo": custo, "teorico": teorico, "tem_ficha": tem_ficha, "margens": margens,
                      "markup": p["preco"] / custo if custo else None})
    return render_template("estoque/produtos.html", produtos=lista, canais=canais)


@bp.route("/produtos/novo", methods=["GET", "POST"])
@bp.route("/produtos/<int:pid>", methods=["GET", "POST"])
def produto_form(pid=None):
    conn = get_db()
    p = conn.execute("SELECT * FROM produtos WHERE id = ?", (pid,)).fetchone() if pid else None
    if request.method == "POST":
        try:
            nome = campo("nome")
            if not nome:
                raise ErroFormulario("Dê um nome ao produto.")
            preco = dinheiro("preco", 0)
            kit = int(inteiro("sabores_por_kit", 0) or 0) if request.form.get("eh_kit") == "1" else 0
            rendimento = 1 if kit else (numero("rendimento", 1) or 1)
            ativo = 0 if request.form.get("inativo") else 1
            if p:
                conn.execute("UPDATE produtos SET nome=?, preco=?, rendimento=?, sabores_por_kit=?, ativo=? WHERE id=?",
                             (nome, preco, rendimento, kit, ativo, pid))
            else:
                pid = conn.execute("INSERT INTO produtos (nome, preco, rendimento, sabores_por_kit) VALUES (?, ?, ?, ?)",
                                   (nome, preco, rendimento, kit)).lastrowid
            linhas = []
            ids = request.form.getlist("ficha_insumo")
            qtds = request.form.getlist("ficha_qtd")
            for i, iid in enumerate(ids):
                if iid:
                    q = numero("_", origem={"_": qtds[i] if i < len(qtds) else ""})
                    linhas.append((int(iid), q))
            se.salvar_ficha(conn, pid, linhas)
            conn.commit()
            ok("Produto salvo.")
            return redirect(url_for("estoque.produto_form", pid=pid))
        except ErroFormulario as e:
            conn.rollback()
            erro(e)
    insumos = conn.execute("SELECT * FROM insumos WHERE ativo = 1 ORDER BY categoria, nome").fetchall()
    ficha = se.ficha(conn, pid) if p else []
    custo_lote = sum(l.custo for l in ficha)
    dados = [{"id": i["id"], "nome": i["nome"], "unidade": i["unidade"], "custo": i["custo_medio"]} for i in insumos]
    canais = conn.execute("SELECT * FROM canais WHERE ativo = 1 ORDER BY id").fetchall()
    return render_template(
        "estoque/produto_form.html", p=p, ficha=ficha, insumos=insumos, custo_lote=custo_lote,
        custo_unit=se.custo_unitario_produto(conn, pid) if p else 0,
        teorico=se.custo_teorico(conn, pid) if p else 0,
        dados_json=json.dumps(dados),
        canais_json=json.dumps([{"nome": c["nome"], "pct": c["comissao_pct"] + c["taxa_pagamento_pct"], "fixa": c["taxa_fixa"]} for c in canais]),
    )
