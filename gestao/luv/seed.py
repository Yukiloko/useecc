"""Dados iniciais.

`base` cria só a estrutura: contas, categorias, canais com as comissões do
plano e o cardápio com os preços do plano. Nenhum número de venda ou custo.

`demo` monta um banco separado com uma operação fictícia de alguns meses, para
explorar as telas. Tudo nele é exemplo.
"""

import random
from datetime import date, timedelta

from .db import get_config, set_config
from .fmt import hoje
from .services import estoque, financeiro, vendas

CATEGORIAS = {
    "receita": ["Encomendas e eventos", "Outras receitas"],
    "deducao": ["Impostos (DAS MEI)", "Reembolsos · Chegou Inteiro"],
    "custo": ["Gás de cozinha", "Insumos sem controle de estoque"],
    "despesa_variavel": ["Entregas e motoboy", "Taxas de maquininha e Pix"],
    "despesa_fixa": [
        "Anota AI", "Marketing e anúncios", "Energia elétrica", "Internet e celular",
        "Aplicativos (Canva etc.)", "Pró-labore", "Manutenção e utensílios",
    ],
    "receita_financeira": ["Rendimentos"],
    "despesa_financeira": ["Tarifas bancárias", "Juros e multas"],
    "investimento": ["Equipamentos"],
    "aporte": ["Aporte da dona"],
    "retirada": ["Retirada de lucro"],
}

CARDAPIO = [
    # nome, preço (centavos), sabores por kit
    ("Tradicional", 1000, 0),
    ("Red Velvet", 1200, 0),
    ("Brookie", 1200, 0),
    ("Nutella", 1500, 0),
    ("Dupla", 2000, 2),
    ("Caixa Presente", 4500, 4),
]


def base(conn, empresa="LUV Brownies"):
    if get_config(conn, "inicializado"):
        return
    set_config(conn, "empresa", empresa)
    pix = conn.execute("INSERT INTO contas (nome) VALUES ('Conta Pix')").lastrowid
    conn.execute("INSERT INTO contas (nome) VALUES ('Dinheiro')")
    for grupo, nomes in CATEGORIAS.items():
        for nome in nomes:
            conn.execute("INSERT INTO categorias (nome, grupo) VALUES (?, ?)", (nome, grupo))
    financeiro.categoria_sistema(conn, "venda")
    financeiro.categoria_sistema(conn, "estoque")
    # comissões do plano: iFood 23% + 3,2% de pagamento online. Prazo de repasse: ajuste ao seu contrato.
    conn.execute(
        "INSERT INTO canais (nome, comissao_pct, taxa_pagamento_pct, prazo_dias, conta_id) VALUES (?, ?, ?, ?, ?)",
        ("iFood", 23.0, 3.2, 30, pix),
    )
    conn.execute(
        "INSERT INTO canais (nome, comissao_pct, taxa_pagamento_pct, prazo_dias, conta_id) VALUES (?, ?, ?, ?, ?)",
        ("WhatsApp · Anota AI", 0, 0, 0, pix),
    )
    for nome, preco, kit in CARDAPIO:
        conn.execute(
            "INSERT INTO produtos (nome, preco, rendimento, sabores_por_kit) VALUES (?, ?, ?, ?)",
            (nome, preco, 1, kit),
        )
    set_config(conn, "inicializado", "1")
    conn.commit()


# ---------------------------------------------------------------- demonstração

INSUMOS_DEMO = [
    # nome, categoria, unidade, custo (centavos por unidade-base), mínimo, compra padrão
    ("Chocolate meio amargo", "ingrediente", "g", 5.5, 1500, 2000),
    ("Manteiga sem sal", "ingrediente", "g", 5.0, 1000, 2000),
    ("Açúcar refinado", "ingrediente", "g", 0.5, 2000, 5000),
    ("Ovos", "ingrediente", "un", 80, 24, 60),
    ("Farinha de trigo", "ingrediente", "g", 0.6, 1000, 5000),
    ("Cacau em pó 50%", "ingrediente", "g", 6.0, 300, 1000),
    ("Creme de avelã (Nutella)", "ingrediente", "g", 7.0, 700, 1400),
    ("Cream cheese", "ingrediente", "g", 4.5, 300, 1200),
    ("Corante vermelho", "ingrediente", "ml", 8.0, 20, 60),
    ("Gotas de chocolate", "ingrediente", "g", 4.5, 300, 1000),
    ("Embalagem individual", "embalagem", "un", 60, 60, 200),
    ("Caixa Dupla", "embalagem", "un", 250, 10, 50),
    ("Caixa Presente", "embalagem", "un", 600, 5, 20),
    ("Cartão escrito à mão", "embalagem", "un", 50, 10, 50),
]

FICHAS_DEMO = {
    # produto: (rendimento, {insumo: quantidade por receita})
    "Tradicional": (12, {"Chocolate meio amargo": 300, "Manteiga sem sal": 200, "Açúcar refinado": 250,
                         "Ovos": 4, "Farinha de trigo": 120, "Cacau em pó 50%": 30, "Embalagem individual": 12}),
    "Red Velvet": (12, {"Chocolate meio amargo": 150, "Manteiga sem sal": 200, "Açúcar refinado": 260,
                        "Ovos": 4, "Farinha de trigo": 180, "Cacau em pó 50%": 15, "Cream cheese": 200,
                        "Corante vermelho": 10, "Embalagem individual": 12}),
    "Brookie": (12, {"Chocolate meio amargo": 200, "Manteiga sem sal": 220, "Açúcar refinado": 260,
                     "Ovos": 4, "Farinha de trigo": 200, "Gotas de chocolate": 150, "Embalagem individual": 12}),
    "Nutella": (12, {"Chocolate meio amargo": 300, "Manteiga sem sal": 200, "Açúcar refinado": 220,
                     "Ovos": 4, "Farinha de trigo": 120, "Cacau em pó 50%": 30,
                     "Creme de avelã (Nutella)": 360, "Embalagem individual": 12}),
    "Dupla": (1, {"Caixa Dupla": 1}),
    "Caixa Presente": (1, {"Caixa Presente": 1, "Cartão escrito à mão": 1}),
}

RECORRENCIAS_DEMO = [
    ("Anota AI", 12990, "Anota AI", 10),
    ("Meta Ads", 20000, "Marketing e anúncios", 5),
    ("Energia (parte da cozinha)", 12000, "Energia elétrica", 15),
    ("Internet e celular", 9900, "Internet e celular", 20),
    ("Canva Pro", 3490, "Aplicativos (Canva etc.)", 12),
    ("DAS MEI", 8090, "Impostos (DAS MEI)", 20),
    ("Pró-labore", 60000, "Pró-labore", 5),
]


def demo(conn, inicio=None, semente=7):
    """Simula uma operação de brownies do `inicio` até hoje. Tudo fictício."""
    base(conn)
    set_config(conn, "demo", "1")
    rnd = random.Random(semente)
    h = hoje()
    inicio = inicio or date(h.year, h.month, 1) - timedelta(days=95)
    inicio = date(inicio.year, inicio.month, 1)

    cat = {r["nome"]: r["id"] for r in conn.execute("SELECT id, nome FROM categorias")}
    conta = conn.execute("SELECT id FROM contas ORDER BY id LIMIT 1").fetchone()["id"]
    dinheiro = conn.execute("SELECT id FROM contas ORDER BY id LIMIT 1 OFFSET 1").fetchone()["id"]

    insumo_id = {}
    compra_padrao = {}
    for nome, categoria, unidade, custo, minimo, compra in INSUMOS_DEMO:
        insumo_id[nome] = conn.execute(
            "INSERT INTO insumos (nome, categoria, unidade, estoque_minimo, custo_medio, fornecedor) VALUES (?, ?, ?, ?, ?, ?)",
            (nome, categoria, unidade, minimo, custo, "Atacadão" if categoria == "ingrediente" else "Casa das Embalagens"),
        ).lastrowid
        compra_padrao[nome] = (compra, custo)

    produto = {r["nome"]: r for r in conn.execute("SELECT * FROM produtos")}
    for nome, (rend, itens) in FICHAS_DEMO.items():
        conn.execute("UPDATE produtos SET rendimento = ? WHERE id = ?", (rend, produto[nome]["id"]))
        estoque.salvar_ficha(conn, produto[nome]["id"], [(insumo_id[i], q) for i, q in itens.items()])
    produto = {r["nome"]: r for r in conn.execute("SELECT * FROM produtos")}
    sabores = [n for n in ("Tradicional", "Red Velvet", "Brookie", "Nutella")]

    for desc, valor, categoria, dia in RECORRENCIAS_DEMO:
        conn.execute(
            "INSERT INTO recorrencias (descricao, valor, categoria_id, conta_id, dia) VALUES (?, ?, ?, ?, ?)",
            (desc, valor, cat[categoria], conta, dia),
        )

    financeiro.salvar_lancamento(conn, {
        "descricao": "Aporte inicial", "valor": 250000, "categoria_id": cat["Aporte da dona"], "conta_id": conta,
        "competencia": inicio.isoformat(), "vencimento": inicio.isoformat(), "pagamento": inicio.isoformat(),
    })
    financeiro.salvar_lancamento(conn, {
        "descricao": "Batedeira planetária", "valor": 45000, "categoria_id": cat["Equipamentos"], "conta_id": conta,
        "competencia": inicio.isoformat(), "vencimento": inicio.isoformat(), "pagamento": inicio.isoformat(),
    })
    conn.execute("UPDATE contas SET saldo_inicial = 15000 WHERE id = ?", (dinheiro,))

    canais = {r["nome"]: r["id"] for r in conn.execute("SELECT id, nome FROM canais")}
    mix = [("Tradicional", 30), ("Red Velvet", 16), ("Brookie", 16), ("Nutella", 18), ("Dupla", 14), ("Caixa Presente", 6)]
    nomes_mix = [m[0] for m in mix]
    pesos_mix = [m[1] for m in mix]

    def comprar(d, nomes, fornecedor):
        itens = []
        for nome in nomes:
            q, custo = compra_padrao[nome]
            custo_real = custo * rnd.uniform(0.95, 1.08)
            itens.append((insumo_id[nome], q, round(q * custo_real)))
        if itens:
            estoque.registrar_compra(conn, d.isoformat(), itens, fornecedor=fornecedor, conta_id=conta, pago=True)

    def compra_da_semana(d):
        # o mercado é feito às segundas e quintas, para o que está perto do mínimo
        faltando = [r["nome"] for r in conn.execute("SELECT nome FROM insumos WHERE estoque < estoque_minimo * 1.2")]
        comprar(d, faltando, "Atacadão")

    def garantir_estoque(d, nome, minimo=8):
        p = conn.execute("SELECT estoque, id FROM produtos WHERE nome = ?", (nome,)).fetchone()
        if p["estoque"] < minimo:
            # faltou algo no meio da semana: compra avulsa só do necessário
            falta = [r["nome"] for r in estoque.necessidade(conn, p["id"], 1) if r["falta"] > 0]
            comprar(d, falta, "Mercado do bairro")
            estoque.registrar_producao(conn, d.isoformat(), p["id"], 1)

    d = inicio
    mes_corrente = None
    while d <= h:
        if (d.year, d.month) != mes_corrente:
            mes_corrente = (d.year, d.month)
            financeiro.gerar_recorrencias(conn, d.year, d.month)
            conn.execute(
                "UPDATE lancamentos SET pagamento = vencimento WHERE origem = 'recorrente' AND pagamento IS NULL AND vencimento < ?",
                (h.isoformat(),),
            )
        if d.weekday() in (0, 3) or d == inicio:
            compra_da_semana(d)
        # crescimento suave mês a mês e fim de semana mais forte
        meses_passados = (d.year - inicio.year) * 12 + d.month - inicio.month
        base_pedidos = 3 + meses_passados * 1.2 + (2.5 if d.weekday() >= 4 else 0)
        pedidos = max(0, int(rnd.gauss(base_pedidos, 1.5)))
        for _ in range(pedidos):
            canal = "iFood" if rnd.random() < max(0.35, 0.7 - meses_passados * 0.08) else "WhatsApp · Anota AI"
            itens = []
            for _ in range(rnd.choice([1, 1, 1, 2])):
                nome = rnd.choices(nomes_mix, pesos_mix)[0]
                p = produto[nome]
                if p["sabores_por_kit"]:
                    escolha = [rnd.choice(sabores) for _ in range(p["sabores_por_kit"])]
                    for s in escolha:
                        garantir_estoque(d, s)
                    itens.append({"produto_id": p["id"], "quantidade": 1,
                                  "sabores": [produto[s]["id"] for s in escolha]})
                else:
                    garantir_estoque(d, nome)
                    itens.append({"produto_id": p["id"], "quantidade": rnd.choice([1, 1, 2])})
            vencimento = d + timedelta(days=30 if canal == "iFood" else 0)
            vendas.registrar_venda(conn, d.isoformat(), canais[canal], itens,
                                   recebido=vencimento <= h)
        if rnd.random() < 0.05:
            s = rnd.choice(sabores)
            if produto[s]["id"]:
                estoque.ajustar(conn, d.isoformat(), "produto", produto[s]["id"], "perda", 1, "Quebrou na entrega")
        if rnd.random() < 0.04:
            financeiro.salvar_lancamento(conn, {
                "descricao": "Botijão de gás", "valor": 11000, "categoria_id": cat["Gás de cozinha"], "conta_id": conta,
                "competencia": d.isoformat(), "vencimento": d.isoformat(), "pagamento": d.isoformat(),
            })
        d += timedelta(days=1)

    # fim de semana chegando: algumas coisas acabaram de ficar abaixo do mínimo
    ontem = (h - timedelta(days=1)).isoformat()
    cc = conn.execute("SELECT estoque FROM insumos WHERE id = ?", (insumo_id["Cream cheese"],)).fetchone()[0]
    if cc > 150:
        estoque.ajustar(conn, ontem, "insumo", insumo_id["Cream cheese"], "perda", cc - 150, "Passou da validade")
    estoque.ajustar(conn, ontem, "insumo", insumo_id["Caixa Presente"], "contagem", 3, "Contagem de estoque")

    # um reembolso da garantia e uma conta a pagar adiante
    financeiro.salvar_lancamento(conn, {
        "descricao": "Chegou Inteiro · reembolso Pix", "valor": 1200, "categoria_id": cat["Reembolsos · Chegou Inteiro"],
        "conta_id": conta, "competencia": (h - timedelta(days=3)).isoformat(),
        "vencimento": (h - timedelta(days=3)).isoformat(), "pagamento": (h - timedelta(days=3)).isoformat(),
    })
    proximo = (h + timedelta(days=9)).isoformat()
    financeiro.salvar_lancamento(conn, {
        "descricao": "Formas e espátulas novas", "valor": 18900, "categoria_id": cat["Manutenção e utensílios"],
        "conta_id": conta, "competencia": proximo, "vencimento": proximo, "pagamento": None,
    })
    conn.commit()
