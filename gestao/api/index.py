"""Entrada do Vercel: todas as rotas caem aqui (ver vercel.json)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wsgi import app  # noqa: E402,F401
