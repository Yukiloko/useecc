from flask import Blueprint, redirect, render_template, request, url_for

from ..db import get_db, set_config
from ..fmt import brl, hoje
from ..services import financeiro as sf
from ._util import ErroFormulario, campo, dinheiro, erro, inteiro, numero, ok

bp = Blueprint("config", __name__, url_prefix="/configuracoes")


@bp.route("/")
def index():
    conn = get_db()
    hoje_iso = hoje().isoformat()
    contas = [{**dict(c), "saldo": sf.saldo_em(conn, hoje_iso, c["id"])}
              for c in conn.execute("SELECT * FROM contas ORDER BY ativa DESC, id")]
    canais = conn.execute(
        "SELECT c.*, ct.nome AS conta FROM canais c LEFT JOIN contas ct ON ct.id = c.conta_id ORDER BY c.ativo DESC, c.id"
    ).fetchall()
    uso = {r["categoria_id"]: r["n"] for r in conn.execute(
        "SELECT categoria_id, COUNT(*) n FROM lancamentos GROUP BY categoria_id")}
    return render_template(
        "config.html", contas=contas, canais=canais, categorias=sf.categorias_por_grupo(conn),
        grupos=sf.GRUPOS, editaveis=sf.GRUPOS_EDITAVEIS, uso=uso, editar=request.args.get("editar", ""),
    )


@bp.route("/empresa", methods=["POST"])
def empresa():
    conn = get_db()
    nome = campo("empresa")
    if nome:
        set_config(conn, "empresa", nome)
        conn.commit()
        ok("Nome atualizado.")
    return redirect(url_for("config.index"))


@bp.route("/contas", methods=["POST"])
def conta_salvar():
    conn = get_db()
    try:
        nome = campo("nome")
        if not nome:
            raise ErroFormulario("Dê um nome à conta.")
        saldo = dinheiro("saldo_inicial", 0)
        cid = inteiro("id")
        if cid:
            conn.execute("UPDATE contas SET nome=?, saldo_inicial=?, ativa=? WHERE id=?",
                         (nome, saldo, 0 if request.form.get("inativa") else 1, cid))
        else:
            conn.execute("INSERT INTO contas (nome, saldo_inicial) VALUES (?, ?)", (nome, saldo))
        conn.commit()
        ok("Conta salva.")
    except ErroFormulario as e:
        erro(e)
    return redirect(url_for("config.index") + "#contas")


@bp.route("/contas/<int:cid>/acertar", methods=["POST"])
def conta_acertar(cid):
    """Recalcula o saldo inicial para o saldo de hoje bater com o extrato do banco."""
    conn = get_db()
    try:
        real = dinheiro("saldo_real", obrigatorio=True)
        novo = sf.acertar_saldo(conn, cid, real)
        conn.commit()
        ok(f"Pronto: o saldo de hoje agora é {brl(real)} (saldo inicial ajustado para {brl(novo)}).")
    except ErroFormulario as e:
        erro(e)
    return redirect(url_for("config.index") + "#contas")


@bp.route("/canais", methods=["POST"])
def canal_salvar():
    conn = get_db()
    try:
        nome = campo("nome")
        if not nome:
            raise ErroFormulario("Dê um nome ao canal.")
        valores = (nome, numero("comissao_pct", 0), numero("taxa_pagamento_pct", 0), dinheiro("taxa_fixa", 0),
                   int(numero("prazo_dias", 0)), inteiro("conta_id"))
        cid = inteiro("id")
        if cid:
            conn.execute("UPDATE canais SET nome=?, comissao_pct=?, taxa_pagamento_pct=?, taxa_fixa=?, prazo_dias=?, conta_id=?, ativo=? WHERE id=?",
                         (*valores, 0 if request.form.get("inativo") else 1, cid))
        else:
            conn.execute("INSERT INTO canais (nome, comissao_pct, taxa_pagamento_pct, taxa_fixa, prazo_dias, conta_id) VALUES (?, ?, ?, ?, ?, ?)",
                         valores)
        conn.commit()
        ok("Canal salvo.")
    except ErroFormulario as e:
        erro(e)
    return redirect(url_for("config.index") + "#canais")


@bp.route("/categorias", methods=["POST"])
def categoria_salvar():
    conn = get_db()
    nome = campo("nome")
    grupo = request.form.get("grupo")
    cid = inteiro("id")
    if not nome or grupo not in sf.GRUPOS_EDITAVEIS:
        erro("Informe nome e grupo.")
    elif cid:
        usada = conn.execute("SELECT COUNT(*) FROM lancamentos WHERE categoria_id = ?", (cid,)).fetchone()[0]
        conn.execute("UPDATE categorias SET nome = ?, grupo = ? WHERE id = ? AND sistema = 0", (nome, grupo, cid))
        if usada:
            # mantém a direção dos lançamentos coerente com o novo grupo
            conn.execute("UPDATE lancamentos SET tipo = ? WHERE categoria_id = ?", (sf.direcao(grupo), cid))
        conn.commit()
        ok("Categoria salva.")
    else:
        conn.execute("INSERT INTO categorias (nome, grupo) VALUES (?, ?)", (nome, grupo))
        conn.commit()
        ok("Categoria criada.")
    return redirect(url_for("config.index") + "#categorias")


@bp.route("/categorias/<int:cid>/excluir", methods=["POST"])
def categoria_excluir(cid):
    conn = get_db()
    usada = conn.execute("SELECT COUNT(*) FROM lancamentos WHERE categoria_id = ?", (cid,)).fetchone()[0]
    usada += conn.execute("SELECT COUNT(*) FROM recorrencias WHERE categoria_id = ?", (cid,)).fetchone()[0]
    if usada:
        erro("Essa categoria tem lançamentos. Mude-os de categoria antes de excluir.")
    else:
        conn.execute("DELETE FROM categorias WHERE id = ? AND sistema = 0", (cid,))
        conn.commit()
        ok("Categoria excluída.")
    return redirect(url_for("config.index") + "#categorias")
