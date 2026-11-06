"""Ponto de entrada para hospedagem (PythonAnywhere, Render, Railway…).

Defina a variável LUV_SENHA com a senha de acesso. Sem ela o app não sobe,
para o financeiro nunca ficar aberto na internet.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

if not os.environ.get("LUV_SENHA"):
    raise RuntimeError("Defina LUV_SENHA antes de publicar: é a senha de acesso à gestão.")

os.environ.setdefault("LUV_HTTPS", "1")

from luv import create_app  # noqa: E402

application = app = create_app(demo=os.environ.get("LUV_DEMO") == "1")
