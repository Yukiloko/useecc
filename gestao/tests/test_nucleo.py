"""Testes das regras que decidem os números: custo médio, CMV, caixa e DRE."""

import os
from datetime import date, timedelta

import pytest

from luv import create_app, db, seed
from luv.fmt import brl, hoje, ler_dinheiro, ler_numero, qtd
from luv.services import estoque, financeiro, vendas


PG = os.environ.get("LUV_TEST_PG")  # ex.: postgresql://luv@localhost:5433/luvtest


@pytest.fixture(params=["sqlite", "postgres"])
def alvo(request, tmp_path):
    """Cada teste roda no SQLite e, se LUV_TEST_PG estiver definida, também no Postgres."""
    if request.param == "sqlite":
        return str(tmp_path / "t.db")
    if not PG:
        pytest.skip("defina LUV_TEST_PG para testar no Postgres")
    import psycopg
    with psycopg.connect(PG, autocommit=True) as c:
        c.execute("DROP SCHEMA public CASCADE")
        c.execute("CREATE SCHEMA public")
    return PG


@pytest.fixture
def conn(alvo):
    c = db.connect(alvo)
    db.init_schema(c)
    seed.base(c)
    yield c
    c.close()


def insumo(conn, nome, unidade="g", minimo=0):
    return conn.execute(
        "INSERT INTO insumos (nome, unidade, estoque_minimo) VALUES (?, ?, ?)", (nome, unidade, minimo)
    ).lastrowid


def produto(conn, nome):
    return conn.execute("SELECT * FROM produtos WHERE nome = ?", (nome,)).fetchone()


def canal(conn, nome):
    return conn.execute("SELECT * FROM canais WHERE nome LIKE ?", (nome + "%",)).fetchone()


HOJE = hoje()
D = lambda dias=0: (HOJE + timedelta(days=dias)).isoformat()


# ---------------------------------------------------------------- formatação

def test_formatos_brasileiros():
    assert brl(123456) == "R$ 1.234,56"
    assert brl(-500) == "−R$ 5,00"
    assert ler_dinheiro("1.234,56") == 123456
    assert ler_dinheiro("12") == 1200
    assert ler_dinheiro("12.5") == 1250
    assert ler_numero("1.500") == 1500
    assert ler_numero("0,5") == 0.5
    assert qtd(2500, "g") == "2,5 kg"
    with pytest.raises(ValueError):
        ler_numero("abc")


# ---------------------------------------------------------------- estoque

def test_custo_medio_ponderado(conn):
    choc = insumo(conn, "Chocolate")
    estoque.registrar_compra(conn, D(-2), [(choc, 1000, 5000)])   # R$ 50/kg
    estoque.registrar_compra(conn, D(-1), [(choc, 1000, 7000)])   # R$ 70/kg
    r = conn.execute("SELECT estoque, custo_medio FROM insumos WHERE id = ?", (choc,)).fetchone()
    assert r["estoque"] == 2000
    assert r["custo_medio"] == pytest.approx(6.0)  # R$ 60/kg


def test_compra_gera_saida_no_caixa_e_nao_entra_na_dre(conn):
    choc = insumo(conn, "Chocolate")
    estoque.registrar_compra(conn, D(), [(choc, 1000, 5000)], conta_id=1, pago=True)
    l = conn.execute("SELECT * FROM lancamentos WHERE origem = 'compra'").fetchone()
    assert l["tipo"] == "saida" and l["valor"] == 5000 and l["pagamento"] == D()
    d = financeiro.dre_mes(conn, HOJE.year, HOJE.month)
    assert d["linha"]["lucro_liquido"]["total"] == 0


def test_compra_a_prazo_fica_pendente(conn):
    choc = insumo(conn, "Chocolate")
    estoque.registrar_compra(conn, D(), [(choc, 1000, 5000)], pago=False, vencimento=D(10))
    l = conn.execute("SELECT * FROM lancamentos WHERE origem = 'compra'").fetchone()
    assert l["pagamento"] is None and l["vencimento"] == D(10)


def _brownie_com_ficha(conn, nome="Tradicional"):
    choc = insumo(conn, "Chocolate")
    emb = insumo(conn, "Embalagem", "un")
    estoque.registrar_compra(conn, D(-3), [(choc, 1000, 6000), (emb, 100, 5000)])
    p = produto(conn, nome)
    conn.execute("UPDATE produtos SET rendimento = 10 WHERE id = ?", (p["id"],))
    estoque.salvar_ficha(conn, p["id"], [(choc, 300), (emb, 10)])  # 300 g × 6 + 10 × 50 = 2300 por lote
    return p["id"], choc, emb


def test_producao_baixa_insumos_e_calcula_custo(conn):
    pid, choc, emb = _brownie_com_ficha(conn)
    estoque.registrar_producao(conn, D(-2), pid, 2)
    p = conn.execute("SELECT estoque, custo_medio FROM produtos WHERE id = ?", (pid,)).fetchone()
    assert p["estoque"] == 20
    assert p["custo_medio"] == pytest.approx(230)  # R$ 2,30 por brownie
    assert conn.execute("SELECT estoque FROM insumos WHERE id = ?", (choc,)).fetchone()[0] == 400


def test_producao_sem_insumo_suficiente(conn):
    pid, *_ = _brownie_com_ficha(conn)
    with pytest.raises(estoque.EstoqueInsuficiente):
        estoque.registrar_producao(conn, D(), pid, 5)
    # forçando, registra e deixa negativo
    estoque.registrar_producao(conn, D(), pid, 5, forcar=True)


def test_excluir_producao_devolve_insumos(conn):
    pid, choc, _ = _brownie_com_ficha(conn)
    prod_id = estoque.registrar_producao(conn, D(-2), pid, 1)
    estoque.excluir_producao(conn, prod_id)
    assert conn.execute("SELECT estoque FROM insumos WHERE id = ?", (choc,)).fetchone()[0] == 1000
    assert conn.execute("SELECT estoque FROM produtos WHERE id = ?", (pid,)).fetchone()[0] == 0


def test_perda_entra_no_cmv(conn):
    choc = insumo(conn, "Chocolate")
    estoque.registrar_compra(conn, D(), [(choc, 1000, 5000)])
    estoque.ajustar(conn, D(), "insumo", choc, "perda", 100)
    d = financeiro.dre_mes(conn, HOJE.year, HOJE.month)
    assert d["linha"]["custo"]["total"] == -500


def test_contagem_define_saldo(conn):
    choc = insumo(conn, "Chocolate")
    estoque.registrar_compra(conn, D(), [(choc, 1000, 5000)])
    estoque.ajustar(conn, D(), "insumo", choc, "contagem", 800)
    assert conn.execute("SELECT estoque FROM insumos WHERE id = ?", (choc,)).fetchone()[0] == 800


def test_lista_de_compras(conn):
    choc = insumo(conn, "Chocolate", minimo=500)
    estoque.registrar_compra(conn, D(), [(choc, 200, 1000)])
    lista = estoque.lista_de_compras(conn)
    assert lista[0]["id"] == choc and lista[0]["sugestao"] == 800


# ---------------------------------------------------------------- vendas

def test_venda_ifood_comissao_cmv_e_repasse(conn):
    pid, *_ = _brownie_com_ficha(conn)
    estoque.registrar_producao(conn, D(-2), pid, 1)
    ifood = canal(conn, "iFood")
    vid = vendas.registrar_venda(conn, D(), ifood["id"], [{"produto_id": pid, "quantidade": 2}])
    v = conn.execute("SELECT * FROM vendas WHERE id = ?", (vid,)).fetchone()
    assert v["bruto"] == 2000
    assert v["comissao"] == round(2000 * 0.262)  # 23% + 3,2%
    assert v["cmv"] == 460
    l = conn.execute("SELECT * FROM lancamentos WHERE origem = 'venda'").fetchone()
    assert l["valor"] == 2000 - v["comissao"]
    assert l["pagamento"] is None and l["vencimento"] == D(30)
    assert conn.execute("SELECT estoque FROM produtos WHERE id = ?", (pid,)).fetchone()[0] == 8


def test_venda_whatsapp_entra_no_caixa_na_hora(conn):
    pid, *_ = _brownie_com_ficha(conn)
    whats = canal(conn, "WhatsApp")
    vendas.registrar_venda(conn, D(), whats["id"], [{"produto_id": pid, "quantidade": 1}], desconto=100)
    l = conn.execute("SELECT * FROM lancamentos WHERE origem = 'venda'").fetchone()
    assert l["valor"] == 900 and l["pagamento"] == D()


def test_kit_baixa_sabores_e_embalagem(conn):
    pid, choc, emb = _brownie_com_ficha(conn)
    estoque.registrar_producao(conn, D(-2), pid, 1)
    caixa = insumo(conn, "Caixa dupla", "un")
    estoque.registrar_compra(conn, D(-2), [(caixa, 10, 2500)])
    dupla = produto(conn, "Dupla")
    estoque.salvar_ficha(conn, dupla["id"], [(caixa, 1)])
    whats = canal(conn, "WhatsApp")
    with pytest.raises(ValueError):
        vendas.registrar_venda(conn, D(), whats["id"], [{"produto_id": dupla["id"], "quantidade": 1, "sabores": [pid]}])
    vid = vendas.registrar_venda(conn, D(), whats["id"], [{"produto_id": dupla["id"], "quantidade": 1, "sabores": [pid, pid]}])
    v = conn.execute("SELECT * FROM vendas WHERE id = ?", (vid,)).fetchone()
    assert v["bruto"] == 2000 and v["unidades"] == 2
    assert v["cmv"] == 230 * 2 + 250
    assert conn.execute("SELECT estoque FROM produtos WHERE id = ?", (pid,)).fetchone()[0] == 8
    assert conn.execute("SELECT estoque FROM insumos WHERE id = ?", (caixa,)).fetchone()[0] == 9


def test_excluir_venda_estorna_tudo(conn):
    pid, *_ = _brownie_com_ficha(conn)
    estoque.registrar_producao(conn, D(-2), pid, 1)
    vid = vendas.registrar_venda(conn, D(), canal(conn, "WhatsApp")["id"], [{"produto_id": pid, "quantidade": 3}])
    vendas.excluir_venda(conn, vid)
    assert conn.execute("SELECT estoque FROM produtos WHERE id = ?", (pid,)).fetchone()[0] == 10
    assert conn.execute("SELECT COUNT(*) FROM lancamentos WHERE origem = 'venda'").fetchone()[0] == 0


# ---------------------------------------------------------------- DRE e caixa

def _cat(conn, nome):
    return conn.execute("SELECT id FROM categorias WHERE nome = ?", (nome,)).fetchone()[0]


def test_dre_completa(conn):
    pid, *_ = _brownie_com_ficha(conn)
    estoque.registrar_producao(conn, D(-2), pid, 1)
    vendas.registrar_venda(conn, D(), canal(conn, "iFood")["id"], [{"produto_id": pid, "quantidade": 10}])
    financeiro.salvar_lancamento(conn, {"descricao": "Anota AI", "valor": 12990, "categoria_id": _cat(conn, "Anota AI"),
                                        "competencia": D(), "vencimento": D()})
    financeiro.salvar_lancamento(conn, {"descricao": "DAS", "valor": 500, "categoria_id": _cat(conn, "Impostos (DAS MEI)"),
                                        "competencia": D(), "vencimento": D()})
    financeiro.salvar_lancamento(conn, {"descricao": "Batedeira", "valor": 45000, "categoria_id": _cat(conn, "Equipamentos"),
                                        "competencia": D(), "vencimento": D(), "pagamento": D()})
    d = financeiro.dre_mes(conn, HOJE.year, HOJE.month)
    L = {k: v["total"] for k, v in d["linha"].items()}
    comissao = round(10000 * 0.262)
    assert L["receita"] == 10000
    assert L["deducao"] == -500
    assert L["custo"] == -2300
    assert L["despesa_variavel"] == -comissao
    assert L["margem_contribuicao"] == 10000 - 500 - 2300 - comissao
    assert L["despesa_fixa"] == -12990
    assert L["lucro_liquido"] == L["margem_contribuicao"] - 12990  # investimento fica fora
    ind = d["acumulado"]
    assert ind["ponto_equilibrio"] == pytest.approx(12990 / (L["margem_contribuicao"] / 10000))


def test_saldo_e_fluxo_projetado(conn):
    conn.execute("UPDATE contas SET saldo_inicial = 10000 WHERE id = 1")
    cat = _cat(conn, "Energia elétrica")
    financeiro.salvar_lancamento(conn, {"descricao": "Luz", "valor": 3000, "categoria_id": cat, "conta_id": 1,
                                        "competencia": D(), "vencimento": D(5)})
    assert financeiro.saldo_em(conn, D()) == 10000
    dias = financeiro.fluxo_diario(conn, HOJE, HOJE + timedelta(days=10))
    assert dias[0]["saldo"] == 10000
    assert dias[-1]["projetado"] == 7000


def test_atrasado_entra_no_projetado_de_hoje(conn):
    cat = _cat(conn, "Energia elétrica")
    financeiro.salvar_lancamento(conn, {"descricao": "Luz", "valor": 3000, "categoria_id": cat,
                                        "competencia": D(-10), "vencimento": D(-5)})
    dias = financeiro.fluxo_diario(conn, HOJE, HOJE + timedelta(days=2))
    assert dias[0]["prev_saidas"] == 3000


def test_recorrencias_nao_duplicam(conn):
    conn.execute("INSERT INTO recorrencias (descricao, valor, categoria_id, dia) VALUES ('Anota', 12990, ?, 31)",
                 (_cat(conn, "Anota AI"),))
    assert financeiro.gerar_recorrencias(conn, 2026, 2) == 1
    assert financeiro.gerar_recorrencias(conn, 2026, 2) == 0
    venc = conn.execute("SELECT vencimento FROM lancamentos").fetchone()[0]
    assert venc == "2026-02-28"


# ---------------------------------------------------------------- telas

def test_todas_as_telas_abrem_com_dados_de_exemplo(alvo):
    app = create_app(database=alvo, demo=True, testing=True)
    c = app.test_client()
    for url in ["/", "/vendas/", "/vendas/nova", "/lancamentos", "/lancamentos/novo", "/recorrentes",
                "/fluxo", "/fluxo/anual", "/dre", "/dre?visao=ano", "/dre.csv", "/lancamentos.csv",
                "/estoque", "/estoque/movimentos", "/estoque/insumos/novo", "/estoque/insumos/1",
                "/compras", "/compras/nova?sugestao=1", "/producao", "/produtos", "/produtos/1", "/produtos/5",
                "/configuracoes/"]:
        assert c.get(url).status_code == 200, url


def test_fluxo_de_venda_pelo_formulario(alvo):
    app = create_app(database=alvo, testing=True)
    c = app.test_client()
    r = c.post("/vendas/nova", data={
        "data": D(), "canal_id": "2", "item_produto": ["1"], "item_qtd": ["3"], "item_preco": ["10,00"],
        "item_sabores": [""], "desconto": "", "comissao": "", "comissao_manual": "0", "recebido": "1",
    })
    assert r.status_code == 302
    with app.app_context():
        conn = db.get_db()
        v = conn.execute("SELECT * FROM vendas").fetchone()
        assert v["bruto"] == 3000 and v["comissao"] == 0
    r = c.post("/lancamentos/novo", data={
        "descricao": "Gás", "valor": "110,00", "categoria_id": "5", "competencia": D(), "vencimento": D(), "pago": "1",
    })
    assert r.status_code == 302


# ---------------------------------------------------------------- login

def test_login_protege_tudo(alvo):
    app = create_app(database=alvo, testing=True, senha="brownie123")
    c = app.test_client()
    r = c.get("/dre")
    assert r.status_code == 302 and "/entrar" in r.headers["Location"]
    assert c.post("/vendas/nova", data={}).status_code == 302
    assert c.post("/entrar", data={"senha": "errada"}).status_code == 200
    r = c.post("/entrar", data={"senha": "brownie123", "proximo": "/dre"})
    assert r.status_code == 302 and r.headers["Location"].endswith("/dre")
    assert c.get("/dre").status_code == 200
    c.post("/sair")
    assert c.get("/").status_code == 302


def test_login_nao_redireciona_para_fora(alvo):
    app = create_app(database=alvo, testing=True, senha="x")
    r = app.test_client().post("/entrar", data={"senha": "x", "proximo": "//site-malicioso.com"})
    assert r.headers["Location"] == "/"


def test_sem_senha_fica_aberto_localmente(alvo):
    app = create_app(database=alvo, testing=True, senha="")
    assert app.test_client().get("/").status_code == 200
