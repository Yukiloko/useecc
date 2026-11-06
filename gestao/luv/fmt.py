"""Formatação e leitura de números no padrão brasileiro, e utilitários de data."""

import calendar
import re
from datetime import date, timedelta

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
MESES_LONGOS = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]
UNIDADES = {"g": "g", "ml": "ml", "un": "un"}


def _milhar(valor, casas):
    texto = f"{abs(valor):,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def brl(centavos, sinal=False):
    """1234567 -> 'R$ 12.345,67'."""
    if centavos is None:
        return "—"
    valor = centavos / 100
    texto = f"R$ {_milhar(valor, 2)}"
    if round(valor, 2) < 0:
        return f"−{texto}"
    if sinal and valor > 0:
        return f"+{texto}"
    return texto


def brl_curto(centavos):
    """Para eixos de gráfico: R$ 1,2 mil."""
    valor = (centavos or 0) / 100
    neg = "−" if valor < 0 else ""
    valor = abs(valor)
    if valor >= 1_000_000:
        return f"{neg}{_milhar(valor / 1_000_000, 1)} mi"
    if valor >= 1000:
        return f"{neg}{_milhar(valor / 1000, 1)} mil"
    return f"{neg}{_milhar(valor, 0)}"


def num(valor, casas=0):
    if valor is None:
        return "—"
    texto = _milhar(valor, casas)
    return f"−{texto}" if valor < 0 else texto


def pct(valor, casas=1):
    if valor is None:
        return "—"
    return f"{num(valor * 100, casas)}%"


def qtd(valor, unidade):
    """Quantidade de insumo legível: 2500 g -> '2,5 kg'."""
    if valor is None:
        return "—"
    if unidade == "g" and abs(valor) >= 1000:
        return f"{num(valor / 1000, 2).rstrip('0').rstrip(',')} kg"
    if unidade == "ml" and abs(valor) >= 1000:
        return f"{num(valor / 1000, 2).rstrip('0').rstrip(',')} L"
    casas = 0 if float(valor).is_integer() else 1
    return f"{num(valor, casas)} {UNIDADES.get(unidade, unidade)}"


def custo_unidade(custo_cent, unidade):
    """Custo por unidade-base exibido de forma útil: R$/kg, R$/L ou R$/un."""
    if unidade == "g":
        return f"{brl(custo_cent * 1000)}/kg"
    if unidade == "ml":
        return f"{brl(custo_cent * 1000)}/L"
    return f"{brl(custo_cent)}/un"


_NUM = re.compile(r"^-?[\d.,]+$")


def ler_numero(texto, padrao=None):
    """Aceita '1.234,5', '1234.5', '1234,5', '12'."""
    if texto is None:
        return padrao
    texto = str(texto).strip().replace("R$", "").replace(" ", "")
    if not texto:
        return padrao
    if not _NUM.match(texto):
        raise ValueError(f"Número inválido: {texto}")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif texto.count(".") > 1:
        texto = texto.replace(".", "")
    elif "." in texto:
        inteiro, dec = texto.rsplit(".", 1)
        if len(dec) == 3 and inteiro.lstrip("-") not in ("", "0"):
            # "1.500" no Brasil é mil e quinhentos
            texto = inteiro + dec
    return float(texto)


def ler_dinheiro(texto, padrao=None):
    valor = ler_numero(texto, None)
    if valor is None:
        return padrao
    return round(valor * 100)


def data_br(iso):
    if not iso:
        return "—"
    a, m, d = iso[:10].split("-")
    return f"{d}/{m}/{a}"


def data_curta(iso):
    if not iso:
        return "—"
    a, m, d = iso[:10].split("-")
    return f"{int(d)} {MESES[int(m) - 1]}"


def hoje():
    return date.today()


def mes_atual():
    return hoje().strftime("%Y-%m")


def ler_mes(texto):
    """'2026-11' -> (2026, 11); inválido -> mês atual."""
    try:
        ano, mes = (int(p) for p in str(texto).split("-")[:2])
        if 1 <= mes <= 12 and 2000 <= ano <= 2100:
            return ano, mes
    except (ValueError, AttributeError):
        pass
    h = hoje()
    return h.year, h.month


def limites_mes(ano, mes):
    ultimo = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, 1), date(ano, mes, ultimo)


def mes_deslocado(ano, mes, delta):
    total = ano * 12 + (mes - 1) + delta
    return total // 12, total % 12 + 1


def nome_mes(ano, mes, longo=True):
    nomes = MESES_LONGOS if longo else MESES
    return f"{nomes[mes - 1]} {ano}" if longo else f"{nomes[mes - 1]}"


def somar_dias(iso, dias):
    return (date.fromisoformat(iso) + timedelta(days=dias)).isoformat()


def ler_data(texto, padrao=None):
    try:
        return date.fromisoformat(str(texto).strip()).isoformat()
    except (ValueError, TypeError):
        return padrao


FILTROS = {
    "brl": brl,
    "brl_curto": brl_curto,
    "num": num,
    "pct": pct,
    "data_br": data_br,
    "data_curta": data_curta,
}
