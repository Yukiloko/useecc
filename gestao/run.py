"""Inicia a gestão da LUV Brownies.

    python run.py              seus dados reais (gestao/dados/luv.db)
    python run.py --demo       banco de exemplo com dados fictícios (gestao/dados/demo.db)
    python run.py --demo --recriar   apaga e recria o banco de exemplo
"""

import argparse
import webbrowser
from pathlib import Path
from threading import Timer

from luv import DADOS, create_app


def main():
    p = argparse.ArgumentParser(description="Gestão LUV Brownies")
    p.add_argument("--demo", action="store_true", help="usa o banco de exemplo")
    p.add_argument("--recriar", action="store_true", help="recria o banco de exemplo")
    p.add_argument("--porta", type=int, default=5000)
    p.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 para abrir no celular pela rede de casa")
    p.add_argument("--sem-navegador", action="store_true")
    args = p.parse_args()

    if args.recriar:
        if not args.demo:
            p.error("--recriar só vale com --demo, para não apagar seus dados reais.")
        (DADOS / "demo.db").unlink(missing_ok=True)

    app = create_app(demo=args.demo)
    url = f"http://127.0.0.1:{args.porta}"
    print(f"\n  LUV · Gestão {'(exemplo) ' if args.demo else ''}em {url}\n  Banco: {Path(app.config['DATABASE'])}\n")
    if not args.sem_navegador:
        Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host=args.host, port=args.porta, debug=False)


if __name__ == "__main__":
    main()
