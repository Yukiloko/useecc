"""Estoque de insumos e de produtos acabados.

Toda entrada e saída vira uma linha em `movimentos`. O saldo e o custo médio
de cada item são recalculados repassando os movimentos em ordem de data, o que
mantém o custo médio ponderado correto mesmo quando um lançamento é feito com
data retroativa ou excluído.
"""

from dataclasses import dataclass

from ..fmt import qtd
from .financeiro import categoria_sistema, registrar_aporte

# "inicial" é o estoque contado na data de corte: muda saldo e custo médio, mas não é
# ganho nem perda, então fica fora da DRE (ao contrário de perda e ajustes de contagem).
TIPOS_ENTRADA = {"compra", "producao", "ajuste_entrada", "estorno", "inicial"}
ROTULOS_MOV = {
    "compra": "Compra",
    "producao": "Produção",
    "consumo": "Consumo na produção",
    "venda": "Venda",
    "perda": "Perda",
    "ajuste_entrada": "Ajuste (+)",
    "ajuste_saida": "Ajuste (−)",
    "inicial": "Estoque inicial",
}


class EstoqueInsuficiente(Exception):
    def __init__(self, faltas):
        self.faltas = faltas
        nomes = ", ".join(f"{f['nome']} (precisa {f['precisa']}, tem {f['tem']})" for f in faltas)
        super().__init__(f"Estoque insuficiente: {nomes}")


@dataclass
class LinhaFicha:
    insumo_id: int
    nome: str
    unidade: str
    quantidade: float
    custo_unitario: float

    @property
    def custo(self):
        return self.quantidade * self.custo_unitario


def _tabela(item):
    if item not in ("insumo", "produto"):
        raise ValueError(item)
    return "insumos" if item == "insumo" else "produtos"


def movimentar(conn, data, item, item_id, tipo, quantidade, custo_unitario=None,
               origem=None, origem_id=None, observacao=None):
    """Grava um movimento. Saídas usam o custo médio atual quando não informado."""
    if custo_unitario is None:
        row = conn.execute(f"SELECT custo_medio FROM {_tabela(item)} WHERE id = ?", (item_id,)).fetchone()
        custo_unitario = row["custo_medio"] if row else 0
    conn.execute(
        "INSERT INTO movimentos (data, item, item_id, tipo, quantidade, custo_unitario, origem, origem_id, observacao) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (data, item, item_id, tipo, quantidade, custo_unitario, origem, origem_id, observacao),
    )
    return custo_unitario


def recalcular(conn, item, item_id):
    """Repassa os movimentos do item e grava saldo e custo médio ponderado."""
    saldo = 0.0
    medio = 0.0
    movs = conn.execute(
        "SELECT tipo, quantidade, custo_unitario FROM movimentos WHERE item = ? AND item_id = ? ORDER BY data, id",
        (item, item_id),
    ).fetchall()
    for m in movs:
        q = m["quantidade"]
        if q > 0 and m["tipo"] in TIPOS_ENTRADA:
            if saldo <= 0:
                medio = m["custo_unitario"]
            else:
                medio = (saldo * medio + q * m["custo_unitario"]) / (saldo + q)
        saldo += q
    if abs(saldo) < 1e-9:
        saldo = 0.0
    if not movs:
        # sem histórico, preserva o custo cadastrado à mão
        medio = conn.execute(f"SELECT custo_medio FROM {_tabela(item)} WHERE id = ?", (item_id,)).fetchone()["custo_medio"]
    conn.execute(f"UPDATE {_tabela(item)} SET estoque = ?, custo_medio = ? WHERE id = ?", (saldo, medio, item_id))


def _recalcular_origem(conn, origem, origem_id):
    afetados = conn.execute(
        "SELECT DISTINCT item, item_id FROM movimentos WHERE origem = ? AND origem_id = ?", (origem, origem_id)
    ).fetchall()
    return [(a["item"], a["item_id"]) for a in afetados]


def desfazer_origem(conn, origem, origem_id):
    afetados = _recalcular_origem(conn, origem, origem_id)
    conn.execute("DELETE FROM movimentos WHERE origem = ? AND origem_id = ?", (origem, origem_id))
    conn.execute("DELETE FROM lancamentos WHERE origem = ? AND origem_id = ?", (origem, origem_id))
    for item, item_id in afetados:
        recalcular(conn, item, item_id)


# ---------------------------------------------------------------- fichas técnicas

def ficha(conn, produto_id):
    rows = conn.execute(
        "SELECT f.insumo_id, i.nome, i.unidade, f.quantidade, i.custo_medio "
        "FROM ficha_tecnica f JOIN insumos i ON i.id = f.insumo_id WHERE f.produto_id = ? ORDER BY i.categoria, i.nome",
        (produto_id,),
    ).fetchall()
    return [LinhaFicha(r["insumo_id"], r["nome"], r["unidade"], r["quantidade"], r["custo_medio"]) for r in rows]


def custo_teorico(conn, produto_id):
    """Custo por unidade pela ficha técnica, com o custo médio atual dos insumos.

    Para kits, soma a embalagem e o custo médio dos sabores (média dos sabores ativos).
    """
    p = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    linhas = ficha(conn, produto_id)
    custo_ficha = sum(l.custo for l in linhas)
    if p["sabores_por_kit"]:
        sabores = conn.execute(
            "SELECT id FROM produtos WHERE ativo = 1 AND sabores_por_kit = 0"
        ).fetchall()
        custos = [custo_unitario_produto(conn, s["id"]) for s in sabores]
        custos = [c for c in custos if c > 0]
        medio = sum(custos) / len(custos) if custos else 0
        return custo_ficha + medio * p["sabores_por_kit"]
    return custo_ficha / (p["rendimento"] or 1)


def custo_unitario_produto(conn, produto_id):
    """Custo médio real se já houve produção; senão o teórico da ficha."""
    p = conn.execute("SELECT custo_medio, sabores_por_kit, rendimento FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    if p["custo_medio"] > 0 and not p["sabores_por_kit"]:
        return p["custo_medio"]
    if p["sabores_por_kit"]:
        return custo_teorico(conn, produto_id)
    return sum(l.custo for l in ficha(conn, produto_id)) / (p["rendimento"] or 1)


def salvar_ficha(conn, produto_id, linhas):
    """linhas: [(insumo_id, quantidade)]"""
    conn.execute("DELETE FROM ficha_tecnica WHERE produto_id = ?", (produto_id,))
    vistos = {}
    for insumo_id, quantidade in linhas:
        if insumo_id and quantidade and quantidade > 0:
            vistos[insumo_id] = vistos.get(insumo_id, 0) + quantidade
    for insumo_id, quantidade in vistos.items():
        conn.execute(
            "INSERT INTO ficha_tecnica (produto_id, insumo_id, quantidade) VALUES (?, ?, ?)",
            (produto_id, insumo_id, quantidade),
        )


# ---------------------------------------------------------------- compras

def registrar_compra(conn, data, itens, fornecedor=None, conta_id=None, vencimento=None,
                     pago=True, observacao=None, bolso=False):
    """itens: [(insumo_id, quantidade, valor_centavos)]. Gera a saída no financeiro.

    bolso=True: a dona pagou com dinheiro próprio; gera também o aporte do mesmo valor.
    """
    pago = pago or bolso
    itens = [(i, q, v) for i, q, v in itens if i and q and q > 0]
    if not itens:
        raise ValueError("Informe ao menos um insumo com quantidade.")
    total = sum(v for _, _, v in itens)
    cur = conn.execute(
        "INSERT INTO compras (data, fornecedor, total, observacao) VALUES (?, ?, ?, ?)",
        (data, fornecedor, total, observacao),
    )
    compra_id = cur.lastrowid
    for insumo_id, quantidade, valor in itens:
        conn.execute(
            "INSERT INTO compra_itens (compra_id, insumo_id, quantidade, valor) VALUES (?, ?, ?, ?)",
            (compra_id, insumo_id, quantidade, valor),
        )
        movimentar(conn, data, "insumo", insumo_id, "compra", quantidade, valor / quantidade, "compra", compra_id)
        if fornecedor:
            conn.execute(
                "UPDATE insumos SET fornecedor = ? WHERE id = ? AND (fornecedor IS NULL OR fornecedor = '')",
                (fornecedor, insumo_id),
            )
        recalcular(conn, "insumo", insumo_id)

    vencimento = vencimento or data
    descricao = f"Compra de insumos{f' · {fornecedor}' if fornecedor else ''}"
    conn.execute(
        "INSERT INTO lancamentos (descricao, valor, tipo, categoria_id, conta_id, competencia, vencimento, pagamento, origem, origem_id) "
        "VALUES (?, ?, 'saida', ?, ?, ?, ?, ?, 'compra', ?)",
        (descricao, total, categoria_sistema(conn, "estoque"), conta_id, data, vencimento,
         data if pago else None, compra_id),
    )
    if bolso:
        registrar_aporte(conn, total, data, conta_id, descricao.lower(), "compra", compra_id)
    return compra_id


def excluir_compra(conn, compra_id):
    desfazer_origem(conn, "compra", compra_id)
    conn.execute("DELETE FROM compras WHERE id = ?", (compra_id,))


# ---------------------------------------------------------------- produção

def necessidade(conn, produto_id, lotes):
    """Insumos necessários para `lotes` receitas, comparados ao estoque."""
    linhas = ficha(conn, produto_id)
    estoque = {r["id"]: r["estoque"] for r in conn.execute("SELECT id, estoque FROM insumos")}
    saida = []
    for l in linhas:
        precisa = l.quantidade * lotes
        tem = estoque.get(l.insumo_id, 0)
        saida.append({
            "insumo_id": l.insumo_id, "nome": l.nome, "unidade": l.unidade,
            "precisa": precisa, "tem": tem, "falta": max(0.0, precisa - tem),
            "custo": precisa * l.custo_unitario,
        })
    return saida


def registrar_producao(conn, data, produto_id, lotes, observacao=None, forcar=False):
    p = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    if p is None:
        raise ValueError("Produto não encontrado.")
    if p["sabores_por_kit"]:
        raise ValueError("Kits são montados na venda, não na produção.")
    if not lotes or lotes <= 0:
        raise ValueError("Informe quantas receitas foram feitas.")
    req = necessidade(conn, produto_id, lotes)
    if not req:
        raise ValueError("Cadastre a ficha técnica do produto antes de registrar a produção.")
    faltas = [
        {"nome": r["nome"], "precisa": qtd(r["precisa"], r["unidade"]), "tem": qtd(r["tem"], r["unidade"])}
        for r in req if r["falta"] > 1e-9
    ]
    if faltas and not forcar:
        raise EstoqueInsuficiente(faltas)

    quantidade = lotes * p["rendimento"]
    cur = conn.execute(
        "INSERT INTO producoes (data, produto_id, lotes, quantidade, observacao) VALUES (?, ?, ?, ?, ?)",
        (data, produto_id, lotes, quantidade, observacao),
    )
    producao_id = cur.lastrowid
    custo_total = 0.0
    for r in req:
        custo = movimentar(conn, data, "insumo", r["insumo_id"], "consumo", -r["precisa"], None, "producao", producao_id)
        custo_total += custo * r["precisa"]
        recalcular(conn, "insumo", r["insumo_id"])
    movimentar(conn, data, "produto", produto_id, "producao", quantidade, custo_total / quantidade, "producao", producao_id)
    recalcular(conn, "produto", produto_id)
    conn.execute("UPDATE producoes SET custo_total = ? WHERE id = ?", (custo_total, producao_id))
    return producao_id


def excluir_producao(conn, producao_id):
    desfazer_origem(conn, "producao", producao_id)
    conn.execute("DELETE FROM producoes WHERE id = ?", (producao_id,))


# ---------------------------------------------------------------- ajustes e perdas

def ajustar(conn, data, item, item_id, tipo, quantidade, observacao=None, custo=None):
    """tipo: 'perda' (sai), 'contagem' (define o saldo contado), 'entrada' (soma) ou
    'inicial' (define o saldo na data de corte, sem passar pela DRE).

    custo: centavos por unidade-base, usado no estoque inicial. Sem ele, vale o custo
    médio atual ou, para produtos ainda não produzidos, o custo da ficha técnica.
    """
    tabela = _tabela(item)
    atual = conn.execute(f"SELECT estoque, custo_medio FROM {tabela} WHERE id = ?", (item_id,)).fetchone()
    if atual is None:
        raise ValueError("Item não encontrado.")
    if tipo == "perda":
        if quantidade <= 0:
            raise ValueError("Informe a quantidade perdida.")
        movimentar(conn, data, item, item_id, "perda", -quantidade, None, "ajuste", None, observacao)
    elif tipo == "contagem":
        delta = quantidade - atual["estoque"]
        if abs(delta) < 1e-9:
            return
        movimentar(conn, data, item, item_id, "ajuste_entrada" if delta > 0 else "ajuste_saida",
                   delta, atual["custo_medio"], "ajuste", None, observacao or "Contagem de estoque")
    elif tipo == "inicial":
        if quantidade < 0:
            raise ValueError("Informe a quantidade que você tem.")
        delta = quantidade - atual["estoque"]
        if abs(delta) < 1e-9:
            return
        if custo is None or custo <= 0:
            custo = atual["custo_medio"]
            if not custo and item == "produto":
                custo = custo_unitario_produto(conn, item_id)
        movimentar(conn, data, item, item_id, "inicial", delta, custo, "ajuste", None, observacao or "Estoque inicial")
    elif tipo == "entrada":
        if quantidade <= 0:
            raise ValueError("Informe a quantidade.")
        movimentar(conn, data, item, item_id, "ajuste_entrada", quantidade, atual["custo_medio"], "ajuste", None, observacao)
    else:
        raise ValueError(tipo)
    recalcular(conn, item, item_id)


def lista_de_compras(conn):
    """Insumos abaixo do mínimo, com sugestão para voltar a 2× o mínimo."""
    rows = conn.execute(
        "SELECT * FROM insumos WHERE ativo = 1 AND estoque_minimo > 0 AND estoque < estoque_minimo ORDER BY nome"
    ).fetchall()
    saida = []
    for r in rows:
        sugestao = r["estoque_minimo"] * 2 - max(r["estoque"], 0)
        saida.append({**dict(r), "sugestao": sugestao, "custo_estimado": sugestao * r["custo_medio"]})
    return saida


def status_insumo(r):
    if r["estoque"] <= 0:
        return "zerado"
    if r["estoque_minimo"] and r["estoque"] < r["estoque_minimo"]:
        return "baixo"
    return "ok"
