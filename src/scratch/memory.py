"""Per-symbol lesson notes persisted across runs (AF4)."""

import json

import tools

MEMORY_PATH = tools.DATA_DIR / "memory.json"


def _read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def load_lessons(symbol, path=MEMORY_PATH):
    return _read(path).get(symbol, [])


def save_lessons(symbol, lessons, path=MEMORY_PATH):
    data = _read(path)
    data[symbol] = list(dict.fromkeys(data.get(symbol, []) + lessons))
    path.write_text(json.dumps(data, indent=2))
    return data[symbol]
