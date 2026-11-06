import os
import secrets
from datetime import timedelta
from pathlib import Path

from flask import Flask, request

from . import db, fmt, seed

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"


def _chave_secreta(conn):
    """Chave das sessões: variável de ambiente ou gerada uma vez e guardada no banco."""
    if os.environ.get("LUV_SECRET"):
        return os.environ["LUV_SECRET"]
    # quem gravar primeiro vence; os outros processos leem a mesma chave
    conn.execute("INSERT INTO config (chave, valor) VALUES (?, ?) ON CONFLICT(chave) DO NOTHING",
                 ("chave_secreta", secrets.token_hex(32)))
    conn.commit()
    return db.get_config(conn, "chave_secreta")


def _banco_padrao(demo):
    """Postgres se houver URL (Vercel + Supabase); senão SQLite em gestao/dados/."""
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if url and not demo:
        return url
    DADOS.mkdir(exist_ok=True)
    return str(DADOS / ("demo.db" if demo else "luv.db"))


def create_app(database=None, demo=False, testing=False, senha=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE=str(database or os.environ.get("LUV_DB") or _banco_padrao(demo)),
        SENHA=senha if senha is not None else os.environ.get("LUV_SENHA", ""),
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=os.environ.get("LUV_HTTPS") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        TESTING=testing,
    )

    conn = db.connect(app.config["DATABASE"])
    db.init_schema(conn, commit=False)   # no Postgres, segura a trava até o commit abaixo
    novo = not db.get_config(conn, "inicializado")
    seed.base(conn, commit=False)
    conn.commit()
    if demo and novo:
        seed.demo(conn)
    app.config["SECRET_KEY"] = _chave_secreta(conn)
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
