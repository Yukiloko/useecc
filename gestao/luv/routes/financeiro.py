import csv
import io
from datetime import timedelta

from flask import Blueprint, Response, redirect, render_template, request, url_for

from .. import charts
from ..db import get_db
from ..fmt import MESES, hoje, limites_mes
from ..services import financeiro as sf
from ._util import (ErroFormulario, campo, data, dinheiro, erro, inteiro, ok,
                    periodo_ano, periodo_mes)

bp = Blueprint("financeiro", __name__)


# ---------------------------------------------------------------- lançamentos

def _filtros_lancamentos():
    per = periodo_mes()
    f = {
        "status": request.args.get("status", ""),
        "tipo": request.args.get("tipo", ""),
        "categoria": request.args.get("categoria", type=int),
        "base": request.args.get("base", "vencimento"),
        "origem": request.args.get("origem", ""),
    }
    return per, f


def _consulta_lancamentos(conn, per, f):
    ini, fim = (d.isoformat() for d in limites_mes(per["ano"], per["mes"]))
    coluna = {"competencia": "l.competencia", "pagamento": "l.pagamento"}.get(f["base"], "l.vencimento")
    where = [f"{coluna} BETWEEN ? AND ?"]
    params = [ini, fim]
    h = hoje().isoformat()
    if f["status"] == "pago":
        where.append("l.pagamento IS NOT NULL")
    elif f["status"] == "pendente":
        where.append("l.pagamento IS NULL")
    elif f["status"] == "atrasado":
        where.append("l.pagamento IS NULL AND l.vencimento < ?")
        params.append(h)
    if f["tipo"] in ("entrada", "saida"):
        where.append("l.tipo = ?")
        params.append(f["tipo"])
    if f["origem"] == "venda":
        where.append("l.origem = 'venda'")
    elif f["origem"] == "outros":
        where.append("l.origem != 'venda'")
    if f["categoria"]:
        where.append("l.categoria_id = ?")
        params.append(f["categoria"])
    return conn.execute(
        "SELECT l.*, c.nome AS categoria, c.grupo, ct.nome AS conta, "
        "(SELECT COUNT(*) FROM lancamentos b WHERE b.origem = 'bolso' AND b.origem_id = l.id) AS do_bolso "
        "FROM lancamentos l "
        "JOIN categorias c ON c.id = l.categoria_id LEFT JOIN contas ct ON ct.id = l.conta_id "
        f"WHERE {' AND '.join(where)} ORDER BY {coluna}, l.id",
        params,
    ).fetchall()


@bp.route("/lancamentos")
def lancamentos():
    conn = get_db()
    per, f = _filtros_lancamentos()
    rows = _consulta_lancamentos(conn, per, f)
    tot = {"entradas": 0, "saidas": 0, "pendente_entrada": 0, "pendente_saida": 0}
    for r in rows:
        chave = "entradas" if r["tipo"] == "entrada" else "saidas"
        tot[chave] += r["valor"]
        if not r["pagamento"]:
            tot["pendente_entrada" if r["tipo"] == "entrada" else "pendente_saida"] += r["valor"]
    return render_template(
        "financeiro/lancamentos.html", per=per, f=f, lancamentos=rows, tot=tot,
        categorias=sf.categorias_por_grupo(conn, incluir_sistema=True), grupos=sf.GRUPOS,
        status=sf.status_lancamento,
    )


@bp.route("/lancamentos.csv")
def lancamentos_csv():
    conn = get_db()
    per, f = _filtros_lancamentos()
    rows = _consulta_lancamentos(conn, per, f)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["Descrição", "Tipo", "Categoria", "Grupo", "Conta", "Valor", "Competência", "Vencimento", "Pagamento", "Origem"])
    for r in rows:
        w.writerow([r["descricao"], r["tipo"], r["categoria"], sf.GRUPOS[r["grupo"]][0], r["conta"] or "",
                    f"{r['valor'] / 100:.2f}".replace(".", ","), r["competencia"], r["vencimento"],
                    r["pagamento"] or "", r["origem"]])
    return _csv(buf, f"lancamentos-{per['chave']}.csv")


def _csv(buf, nome):
    return Response("﻿" + buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={nome}"})


def _form_lancamento(conn, lanc=None, bolso=False):
    if request.method == "POST":
        bolso = request.form.get("bolso") == "1"
    return render_template(
        "financeiro/lancamento_form.html", lanc=lanc, bolso=bolso,
        categorias=sf.categorias_por_grupo(conn), grupos=sf.GRUPOS,
        contas=conn.execute("SELECT * FROM contas WHERE ativa = 1 ORDER BY id").fetchall(),
        tipo_padrao=request.args.get("tipo", "saida"),
    )


def _ler_lancamento():
    competencia = data("competencia")
    vencimento = data("vencimento", competencia)
    bolso = request.form.get("bolso") == "1"
    pago = request.form.get("pago") == "1" or bolso
    return {
        "bolso": bolso,
        "descricao": campo("descricao"),
        "valor": dinheiro("valor", obrigatorio=True),
        "categoria_id": inteiro("categoria_id"),
        "conta_id": inteiro("conta_id"),
        "competencia": competencia,
        "vencimento": vencimento,
        "pagamento": (data("pagamento", vencimento, obrigatorio=False) or vencimento) if pago else None,
        "observacao": campo("observacao"),
    }


@bp.route("/lancamentos/novo", methods=["GET", "POST"])
def lancamento_novo():
    conn = get_db()
    if request.method == "POST":
        try:
            dados = _ler_lancamento()
            if request.form.get("parcelar") == "1":
                n = inteiro("parcelas", 0) or 0
                sf.salvar_parcelado(conn, {**dados, "pagamento": None}, n)
                conn.commit()
                ok(f"{n} parcelas criadas, a primeira vencendo em {dados['vencimento'][8:]}/{dados['vencimento'][5:7]}.")
                if request.form.get("continuar"):
                    return redirect(url_for("financeiro.lancamento_novo"))
                return redirect(url_for("financeiro.lancamentos", mes=dados["vencimento"][:7]))
            lid = sf.salvar_lancamento(conn, dados)
            sf.sincronizar_bolso(conn, lid, dados["bolso"])
            conn.commit()
            ok("Lançamento salvo.")
            if request.form.get("continuar"):
                return redirect(url_for("financeiro.lancamento_novo"))
            return redirect(url_for("financeiro.lancamentos", mes=dados["vencimento"][:7]))
        except (ErroFormulario, ValueError) as e:
            conn.rollback()
            erro(e)
    return _form_lancamento(conn)


@bp.route("/lancamentos/<int:lid>", methods=["GET", "POST"])
def lancamento_editar(lid):
    conn = get_db()
    lanc = conn.execute("SELECT * FROM lancamentos WHERE id = ?", (lid,)).fetchone()
    if lanc is None:
        return redirect(url_for("financeiro.lancamentos"))
    if lanc["origem"] == "bolso":
        # o aporte automático é editado pela despesa que o gerou
        return redirect(url_for("financeiro.lancamento_editar", lid=lanc["origem_id"]))
    if lanc["origem"] in ("venda", "compra") and request.method == "POST":
        # gerado automaticamente: só data e conta de pagamento são editáveis
        try:
            pago = request.form.get("pago") == "1"
            pagamento = (data("pagamento", lanc["vencimento"], obrigatorio=False) or lanc["vencimento"]) if pago else None
            conn.execute("UPDATE lancamentos SET vencimento = ?, pagamento = ?, conta_id = ? WHERE id = ?",
                         (data("vencimento", lanc["vencimento"]), pagamento, inteiro("conta_id"), lid))
            conn.commit()
            ok("Lançamento atualizado.")
            return redirect(url_for("financeiro.lancamentos", mes=lanc["vencimento"][:7]))
        except ErroFormulario as e:
            erro(e)
    elif request.method == "POST":
        try:
            dados = _ler_lancamento()
            sf.salvar_lancamento(conn, dados, lid)
            sf.sincronizar_bolso(conn, lid, dados["bolso"])
            conn.commit()
            ok("Lançamento atualizado.")
            return redirect(url_for("financeiro.lancamentos", mes=dados["vencimento"][:7]))
        except (ErroFormulario, ValueError) as e:
            conn.rollback()
            erro(e)
    return _form_lancamento(conn, lanc, bolso=sf.tem_bolso(conn, lid))


@bp.route("/lancamentos/<int:lid>/pagar", methods=["POST"])
def lancamento_pagar(lid):
    conn = get_db()
    l = conn.execute("SELECT * FROM lancamentos WHERE id = ?", (lid,)).fetchone()
    if l:
        if l["pagamento"]:
            conn.execute("UPDATE lancamentos SET pagamento = NULL WHERE id = ?", (lid,))
            # se tinha sido pago do bolso, o aporte deixa de existir
            sf.sincronizar_bolso(conn, lid, False)
            ok("Voltou para pendente.")
        else:
            conn.execute("UPDATE lancamentos SET pagamento = ? WHERE id = ?", (hoje().isoformat(), lid))
            ok("Recebido." if l["tipo"] == "entrada" else "Pago.")
        conn.commit()
    return redirect(request.referrer or url_for("financeiro.lancamentos"))


@bp.route("/lancamentos/baixa", methods=["POST"])
def lancamentos_baixa():
    """Marca vários lançamentos como pagos/recebidos numa data (ex.: repasse semanal do iFood)."""
    conn = get_db()
    ids = [int(i) for i in request.form.getlist("ids") if i.isdigit()]
    quando = data("pagamento", hoje().isoformat(), obrigatorio=False) or hoje().isoformat()
    if ids:
        marcas = ",".join("?" * len(ids))
        conn.execute(f"UPDATE lancamentos SET pagamento = ? WHERE pagamento IS NULL AND id IN ({marcas})", [quando, *ids])
        conn.commit()
        ok(f"{len(ids)} lançamento(s) baixados em {quando[8:]}/{quando[5:7]}.")
    else:
        erro("Selecione ao menos um lançamento.")
    return redirect(request.referrer or url_for("financeiro.lancamentos"))


@bp.route("/lancamentos/<int:lid>/excluir", methods=["POST"])
def lancamento_excluir(lid):
    conn = get_db()
    l = conn.execute("SELECT * FROM lancamentos WHERE id = ?", (lid,)).fetchone()
    if l and l["origem"] in ("venda", "compra"):
        erro("Esse lançamento vem de uma venda ou compra. Exclua a venda ou a compra.")
    elif l and l["origem"] == "bolso":
        erro("Esse aporte foi criado por uma despesa paga do seu bolso. Edite ou exclua a despesa.")
    elif l:
        conn.execute("DELETE FROM lancamentos WHERE (origem = 'bolso' AND origem_id = ?) OR id = ?", (lid, lid))
        conn.commit()
        ok("Lançamento excluído.")
    return redirect(url_for("financeiro.lancamentos", mes=l["vencimento"][:7] if l else None))


# ---------------------------------------------------------------- recorrências

@bp.route("/recorrentes", methods=["GET", "POST"])
def recorrentes():
    conn = get_db()
    if request.method == "POST":
        try:
            rid = inteiro("id")
            valores = (campo("descricao") or "", dinheiro("valor", obrigatorio=True), inteiro("categoria_id"),
                       inteiro("conta_id"), max(1, min(31, inteiro("dia", 5))), 1 if request.form.get("ativa", "1") == "1" else 0,
                       1 if request.form.get("mes_seguinte") == "1" else 0)
            if not valores[0] or not valores[2]:
                raise ErroFormulario("Preencha descrição e categoria.")
            if rid:
                conn.execute("UPDATE recorrencias SET descricao=?, valor=?, categoria_id=?, conta_id=?, dia=?, ativa=?, mes_seguinte=? WHERE id=?",
                             (*valores, rid))
            else:
                conn.execute("INSERT INTO recorrencias (descricao, valor, categoria_id, conta_id, dia, ativa, mes_seguinte) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             valores)
            conn.commit()
            ok("Recorrência salva.")
            return redirect(url_for("financeiro.recorrentes"))
        except ErroFormulario as e:
            erro(e)
    rows = conn.execute(
        "SELECT r.*, c.nome AS categoria, c.grupo, ct.nome AS conta FROM recorrencias r "
        "JOIN categorias c ON c.id = r.categoria_id LEFT JOIN contas ct ON ct.id = r.conta_id ORDER BY r.ativa DESC, r.dia"
    ).fetchall()
    per = periodo_mes()
    gerados = {r["origem_id"] for r in conn.execute(
        "SELECT origem_id FROM lancamentos WHERE origem = 'recorrente' AND substr(competencia, 1, 7) = ?", (per["chave"],))}
    return render_template(
        "financeiro/recorrentes.html", recorrencias=rows, per=per, gerados=gerados,
        categorias=sf.categorias_por_grupo(conn), grupos=sf.GRUPOS,
        contas=conn.execute("SELECT * FROM contas WHERE ativa = 1").fetchall(),
        total=sum(r["valor"] for r in rows if r["ativa"]),
        editar=request.args.get("editar", type=int),
    )


@bp.route("/recorrentes/gerar", methods=["POST"])
def recorrentes_gerar():
    conn = get_db()
    per = periodo_mes() if request.args.get("mes") else None
    chave = request.form.get("mes") or (per["chave"] if per else hoje().strftime("%Y-%m"))
    ano, mes = (int(p) for p in chave.split("-"))
    n = sf.gerar_recorrencias(conn, ano, mes)
    conn.commit()
    ok(f"{n} lançamento(s) criados para {chave[5:]}/{chave[:4]}." if n else "Os lançamentos desse mês já existem.")
    return redirect(url_for("financeiro.lancamentos", mes=chave))


@bp.route("/recorrentes/<int:rid>/excluir", methods=["POST"])
def recorrente_excluir(rid):
    conn = get_db()
    conn.execute("DELETE FROM recorrencias WHERE id = ?", (rid,))
    conn.commit()
    ok("Recorrência removida. Os lançamentos já gerados continuam.")
    return redirect(url_for("financeiro.recorrentes"))


# ---------------------------------------------------------------- fluxo de caixa

@bp.route("/fluxo")
def fluxo():
    conn = get_db()
    per = periodo_mes()
    ini, fim = limites_mes(per["ano"], per["mes"])
    dias = sf.fluxo_diario(conn, ini, fim)
    contas, sem_conta = sf.saldos_contas(conn)
    tot = {
        "entradas": sum(d["entradas"] for d in dias),
        "saidas": sum(d["saidas"] for d in dias),
        "prev_entradas": sum(d["prev_entradas"] for d in dias),
        "prev_saidas": sum(d["prev_saidas"] for d in dias),
    }
    inicial = sf.saldo_em(conn, (ini - timedelta(days=1)).isoformat())
    final_proj = next((d["projetado"] for d in reversed(dias) if d["projetado"] is not None), None)
    final_real = next((d["saldo"] for d in reversed(dias) if d["saldo"] is not None), None)
    rotulos = [str(int(d["data"][8:])) for d in dias]
    grafico_mov = charts.barras(
        rotulos,
        [("Entradas", [d["entradas"] + d["prev_entradas"] for d in dias], "s-entrada"),
         ("Saídas", [-(d["saidas"] + d["prev_saidas"]) for d in dias], "s-saida")],
        altura=200, mostrar_cada=3,
    )
    grafico_saldo = charts.linhas(
        rotulos,
        [("Saldo realizado", [d["saldo"] for d in dias], "s-saldo area"),
         ("Saldo previsto", [d["projetado"] if d["futuro"] or d["data"] == hoje().isoformat() else None for d in dias], "s-previsto")],
        altura=200, mostrar_cada=3,
    )
    return render_template(
        "financeiro/fluxo.html", per=per, dias=dias, tot=tot, contas=contas, sem_conta=sem_conta,
        saldo_total=sum(c["saldo"] for c in contas) + sem_conta,
        inicial=inicial, final_proj=final_proj, final_real=final_real,
        grafico_mov=grafico_mov, grafico_saldo=grafico_saldo,
    )


@bp.route("/fluxo/anual")
def fluxo_anual():
    conn = get_db()
    per = periodo_ano()
    f = sf.fluxo_mensal(conn, per["ano"])
    grafico = charts.barras(
        MESES, [("Geração de caixa", f["geracao"], "s-lucro")], altura=200,
    )
    grafico_saldo = charts.linhas(MESES, [("Saldo final", f["saldo_final"], "s-saldo area")], altura=200)
    return render_template("financeiro/fluxo_anual.html", per=per, f=f, grafico=grafico, grafico_saldo=grafico_saldo)


# ---------------------------------------------------------------- DRE

@bp.route("/dre")
def dre():
    conn = get_db()
    visao = request.args.get("visao", "mes")
    if visao == "ano":
        per = periodo_ano()
        d = sf.dre_ano(conn, per["ano"])
        ind = d["acumulado"]
    else:
        per = periodo_mes()
        meses = sf.ultimos_meses(per["ano"], per["mes"], 2)
        d = sf.dre(conn, meses)
        ind = d["por_mes"][-1]
    grafico = None
    if visao == "ano":
        grafico = charts.barras(
            d["colunas"],
            [("Receita bruta", d["linha"]["receita"]["valores"], "s-receita"),
             ("Margem de contribuição", d["linha"]["margem_contribuicao"]["valores"], "s-mc"),
             ("Lucro líquido", d["linha"]["lucro_liquido"]["valores"], "s-lucro")],
            altura=220,
        )
    return render_template("financeiro/dre.html", d=d, per=per, visao=visao, ind=ind, grafico=grafico)


@bp.route("/dre.csv")
def dre_csv():
    conn = get_db()
    per = periodo_ano()
    d = sf.dre_ano(conn, per["ano"])
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["Linha"] + d["colunas"] + ["Total"])
    fmt = lambda v: f"{v / 100:.2f}".replace(".", ",")
    for l in d["linhas"]:
        w.writerow([l["rotulo"]] + [fmt(v) for v in l["valores"]] + [fmt(l["total"])])
        for i in l["itens"]:
            w.writerow(["   " + i["rotulo"]] + [fmt(v) for v in i["valores"]] + [fmt(i["total"])])
    return _csv(buf, f"dre-{per['ano']}.csv")
