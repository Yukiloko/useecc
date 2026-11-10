-- Valores em dinheiro ficam em centavos (INTEGER). Custos unitários ficam em
-- centavos por unidade-base (REAL), porque 1 g de chocolate custa frações de centavo.
-- Quantidades de insumo ficam na unidade-base: g, ml ou un.

CREATE TABLE IF NOT EXISTS config (
    chave TEXT PRIMARY KEY,
    valor TEXT
);

CREATE TABLE IF NOT EXISTS contas (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    saldo_inicial INTEGER NOT NULL DEFAULT 0,
    ativa INTEGER NOT NULL DEFAULT 1
);

-- grupo decide onde a categoria entra:
--   DRE + caixa: receita, deducao, custo, despesa_variavel, despesa_fixa,
--                receita_financeira, despesa_financeira
--   só caixa:    venda (gerado pelas vendas), estoque (compra de insumos),
--                investimento, aporte, retirada
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    grupo TEXT NOT NULL,
    sistema INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS lancamentos (
    id INTEGER PRIMARY KEY,
    descricao TEXT NOT NULL,
    valor INTEGER NOT NULL CHECK (valor >= 0),
    tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida')),
    categoria_id INTEGER NOT NULL REFERENCES categorias(id),
    conta_id INTEGER REFERENCES contas(id),
    competencia TEXT NOT NULL,
    vencimento TEXT NOT NULL,
    pagamento TEXT,
    origem TEXT NOT NULL DEFAULT 'manual',
    origem_id INTEGER,
    observacao TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_lanc_comp ON lancamentos(competencia);
CREATE INDEX IF NOT EXISTS ix_lanc_pag ON lancamentos(pagamento);
CREATE INDEX IF NOT EXISTS ix_lanc_origem ON lancamentos(origem, origem_id);

CREATE TABLE IF NOT EXISTS recorrencias (
    id INTEGER PRIMARY KEY,
    descricao TEXT NOT NULL,
    valor INTEGER NOT NULL,
    categoria_id INTEGER NOT NULL REFERENCES categorias(id),
    conta_id INTEGER REFERENCES contas(id),
    dia INTEGER NOT NULL DEFAULT 5,
    ativa INTEGER NOT NULL DEFAULT 1,
    -- 1: a conta do mês vence no mês seguinte (ex.: DAS de novembro vence em dezembro)
    mes_seguinte INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS canais (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    comissao_pct REAL NOT NULL DEFAULT 0,
    taxa_pagamento_pct REAL NOT NULL DEFAULT 0,
    taxa_fixa INTEGER NOT NULL DEFAULT 0,
    prazo_dias INTEGER NOT NULL DEFAULT 0,
    conta_id INTEGER REFERENCES contas(id),
    ativo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS insumos (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    categoria TEXT NOT NULL DEFAULT 'ingrediente',
    unidade TEXT NOT NULL DEFAULT 'g',
    estoque REAL NOT NULL DEFAULT 0,
    custo_medio REAL NOT NULL DEFAULT 0,
    estoque_minimo REAL NOT NULL DEFAULT 0,
    fornecedor TEXT,
    ativo INTEGER NOT NULL DEFAULT 1
);

-- sabores_por_kit > 0: o produto é um kit (Dupla, Caixa Presente). Não é
-- produzido em lote; na venda, baixa os sabores escolhidos e a embalagem.
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    preco INTEGER NOT NULL DEFAULT 0,
    rendimento REAL NOT NULL DEFAULT 1,
    sabores_por_kit INTEGER NOT NULL DEFAULT 0,
    estoque REAL NOT NULL DEFAULT 0,
    custo_medio REAL NOT NULL DEFAULT 0,
    ativo INTEGER NOT NULL DEFAULT 1
);

-- quantidade por receita (lote). Para kits, quantidade por kit.
CREATE TABLE IF NOT EXISTS ficha_tecnica (
    produto_id INTEGER NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
    insumo_id INTEGER NOT NULL REFERENCES insumos(id),
    quantidade REAL NOT NULL,
    PRIMARY KEY (produto_id, insumo_id)
);

CREATE TABLE IF NOT EXISTS movimentos (
    id INTEGER PRIMARY KEY,
    data TEXT NOT NULL,
    item TEXT NOT NULL CHECK (item IN ('insumo', 'produto')),
    item_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    quantidade REAL NOT NULL,
    custo_unitario REAL NOT NULL DEFAULT 0,
    origem TEXT,
    origem_id INTEGER,
    observacao TEXT
);
CREATE INDEX IF NOT EXISTS ix_mov_item ON movimentos(item, item_id);
CREATE INDEX IF NOT EXISTS ix_mov_origem ON movimentos(origem, origem_id);

CREATE TABLE IF NOT EXISTS compras (
    id INTEGER PRIMARY KEY,
    data TEXT NOT NULL,
    fornecedor TEXT,
    total INTEGER NOT NULL DEFAULT 0,
    observacao TEXT
);

CREATE TABLE IF NOT EXISTS compra_itens (
    id INTEGER PRIMARY KEY,
    compra_id INTEGER NOT NULL REFERENCES compras(id) ON DELETE CASCADE,
    insumo_id INTEGER NOT NULL REFERENCES insumos(id),
    quantidade REAL NOT NULL,
    valor INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS producoes (
    id INTEGER PRIMARY KEY,
    data TEXT NOT NULL,
    produto_id INTEGER NOT NULL REFERENCES produtos(id),
    lotes REAL NOT NULL,
    quantidade REAL NOT NULL,
    custo_total REAL NOT NULL DEFAULT 0,
    observacao TEXT
);

CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY,
    data TEXT NOT NULL,
    canal_id INTEGER NOT NULL REFERENCES canais(id),
    cliente TEXT,
    bruto INTEGER NOT NULL DEFAULT 0,
    desconto INTEGER NOT NULL DEFAULT 0,
    comissao INTEGER NOT NULL DEFAULT 0,
    cmv INTEGER NOT NULL DEFAULT 0,
    unidades REAL NOT NULL DEFAULT 0,
    observacao TEXT
);
CREATE INDEX IF NOT EXISTS ix_vendas_data ON vendas(data);

CREATE TABLE IF NOT EXISTS venda_itens (
    id INTEGER PRIMARY KEY,
    venda_id INTEGER NOT NULL REFERENCES vendas(id) ON DELETE CASCADE,
    produto_id INTEGER NOT NULL REFERENCES produtos(id),
    quantidade REAL NOT NULL,
    preco_unitario INTEGER NOT NULL,
    custo_unitario REAL NOT NULL DEFAULT 0,
    sabores TEXT
);
