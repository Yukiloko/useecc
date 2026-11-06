import os
from pathlib import Path

from flask import Flask, request

from . import db, fmt, seed

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"


def create_app(database=None, demo=False, testing=False):
    app = Flask(__name__)
    DADOS.mkdir(exist_ok=True)
    padrao = DADOS / ("demo.db" if demo else "luv.db")
    app.config.update(
        DATABASE=str(database or os.environ.get("LUV_DB") or padrao),
        SECRET_KEY=os.environ.get("LUV_SECRET", "luv-local"),
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

    from .routes import config, estoque, financeiro, painel, vendas

    for bp in (painel.bp, vendas.bp, financeiro.bp, estoque.bp, config.bp):
        app.register_blueprint(bp)

    @app.context_processor
    def contexto():
        conn = db.get_db()
        return {
            "empresa": db.get_config(conn, "empresa", "LUV Brownies"),
            "modo_demo": db.get_config(conn, "demo") == "1",
            "hoje_iso": fmt.hoje().isoformat(),
            "endpoint": request.endpoint or "",
        }

    return app
