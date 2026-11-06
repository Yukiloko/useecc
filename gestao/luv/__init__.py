import os
import secrets
from datetime import timedelta
from pathlib import Path

from flask import Flask, request

from . import db, fmt, seed

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"


def _chave_secreta():
    """Chave das sessões: variável de ambiente ou um arquivo gerado na primeira execução."""
    if os.environ.get("LUV_SECRET"):
        return os.environ["LUV_SECRET"]
    arq = DADOS / "chave-secreta.txt"
    if not arq.exists():
        arq.write_text(secrets.token_hex(32), encoding="utf-8")
    return arq.read_text(encoding="utf-8").strip()


def create_app(database=None, demo=False, testing=False, senha=None):
    app = Flask(__name__)
    DADOS.mkdir(exist_ok=True)
    padrao = DADOS / ("demo.db" if demo else "luv.db")
    app.config.update(
        DATABASE=str(database or os.environ.get("LUV_DB") or padrao),
        SECRET_KEY=_chave_secreta(),
        SENHA=senha if senha is not None else os.environ.get("LUV_SENHA", ""),
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=os.environ.get("LUV_HTTPS") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        TESTING=testing,
    )

    conn = db.connect(app.config["DATABASE"])
    db.init_schema(conn)
    novo = not db.get_config(conn, "inicializado")
    if demo and novo:
        seed.demo(conn)
    else:
        seed.base(conn)
    conn.close()

    app.teardown_appcontext(db.close_db)
    app.jinja_env.filters.update(fmt.FILTROS)
    app.jinja_env.filters["qtd"] = fmt.qtd
    app.jinja_env.filters["custo_unidade"] = fmt.custo_unidade

    from . import auth
    from .routes import config, estoque, financeiro, painel, vendas

    for bp in (auth.bp, painel.bp, vendas.bp, financeiro.bp, estoque.bp, config.bp):
        app.register_blueprint(bp)
    app.before_request(auth.proteger)

    @app.context_processor
    def contexto():
        conn = db.get_db()
        return {
            "empresa": db.get_config(conn, "empresa", "LUV Brownies"),
            "modo_demo": db.get_config(conn, "demo") == "1",
            "hoje_iso": fmt.hoje().isoformat(),
            "endpoint": request.endpoint or "",
            "com_login": bool(app.config["SENHA"]),
        }

    return app
