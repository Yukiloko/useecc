"""Login por senha única. Ativo quando LUV_SENHA está definida (obrigatório online)."""

import hmac
import time

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

bp = Blueprint("auth", __name__)

LIVRES = {"auth.entrar", "static"}


def ativo():
    return bool(current_app.config.get("SENHA"))


def proteger():
    """before_request: manda para o login quem não entrou."""
    if not ativo() or request.endpoint in LIVRES or session.get("ok"):
        return None
    if request.method == "GET":
        return redirect(url_for("auth.entrar", proximo=request.full_path.rstrip("?")))
    return redirect(url_for("auth.entrar"))


def _seguro(destino):
    return destino if destino and destino.startswith("/") and not destino.startswith("//") else url_for("painel.index")


@bp.route("/entrar", methods=["GET", "POST"])
def entrar():
    if not ativo():
        return redirect(url_for("painel.index"))
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if hmac.compare_digest(senha.encode(), current_app.config["SENHA"].encode()):
            session.clear()
            session["ok"] = True
            session.permanent = request.form.get("lembrar") == "1"
            return redirect(_seguro(request.form.get("proximo")))
        time.sleep(1.5)  # freia tentativas em sequência
        erro = "Senha incorreta."
    return render_template("entrar.html", erro=erro, proximo=request.values.get("proximo", ""))


@bp.route("/sair", methods=["POST"])
def sair():
    session.clear()
    return redirect(url_for("auth.entrar"))
