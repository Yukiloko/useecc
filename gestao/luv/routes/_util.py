from flask import flash, request

from ..fmt import hoje, ler_data, ler_dinheiro, ler_mes, ler_numero, mes_deslocado, nome_mes


class ErroFormulario(ValueError):
    pass


def campo(nome, padrao=None):
    valor = request.form.get(nome)
    if valor is None:
        return padrao
    valor = valor.strip()
    return valor if valor else padrao


def dinheiro(nome, padrao=None, obrigatorio=False):
    try:
        v = ler_dinheiro(request.form.get(nome), padrao)
    except ValueError:
        raise ErroFormulario(f"Valor inválido em “{rotulo(nome)}”.")
    if obrigatorio and v is None:
        raise ErroFormulario(f"Preencha “{rotulo(nome)}”.")
    return v


def numero(nome, padrao=None, obrigatorio=False, origem=None):
    origem = origem if origem is not None else request.form
    try:
        v = ler_numero(origem.get(nome), padrao)
    except ValueError:
        raise ErroFormulario(f"Número inválido em “{rotulo(nome)}”.")
    if obrigatorio and v is None:
        raise ErroFormulario(f"Preencha “{rotulo(nome)}”.")
    return v


def inteiro(nome, padrao=None):
    try:
        v = request.form.get(nome) or request.args.get(nome)
        return int(v) if v not in (None, "") else padrao
    except ValueError:
        return padrao


def data(nome, padrao=None, obrigatorio=True):
    v = ler_data(request.form.get(nome), padrao)
    if obrigatorio and not v:
        raise ErroFormulario(f"Data inválida em “{rotulo(nome)}”.")
    return v


ROTULOS = {
    "valor": "Valor", "preco": "Preço", "desconto": "Desconto", "comissao": "Comissão",
    "quantidade": "Quantidade", "lotes": "Receitas", "estoque_minimo": "Estoque mínimo",
    "competencia": "Competência", "vencimento": "Vencimento", "data": "Data", "rendimento": "Rendimento",
    "saldo_inicial": "Saldo inicial", "custo_medio": "Custo",
}


def rotulo(nome):
    return ROTULOS.get(nome, nome.replace("_", " ").capitalize())


def periodo_mes():
    """Mês vindo de ?mes=AAAA-MM, com navegação anterior/próximo."""
    ano, mes = ler_mes(request.args.get("mes"))
    pa, pm = mes_deslocado(ano, mes, -1)
    na, nm = mes_deslocado(ano, mes, 1)
    return {
        "ano": ano, "mes": mes, "chave": f"{ano:04d}-{mes:02d}", "nome": nome_mes(ano, mes),
        "anterior": f"{pa:04d}-{pm:02d}", "proximo": f"{na:04d}-{nm:02d}",
        "atual": (ano, mes) == (hoje().year, hoje().month),
    }


def periodo_ano():
    try:
        ano = int(request.args.get("ano", hoje().year))
    except ValueError:
        ano = hoje().year
    return {"ano": ano, "anterior": ano - 1, "proximo": ano + 1, "atual": ano == hoje().year}


def erro(msg):
    flash(str(msg), "erro")


def ok(msg):
    flash(msg, "ok")
