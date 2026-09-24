"""Assemble the scratch modules into a paste-ready notebook (submission step).

Reads the source modules in notebook order, hoists their top-level imports into
one deduped cell, and writes each module body as its own code cell. Lazy
imports inside functions are left untouched. Run it, then copy the cells into
``src/investment_research_agent.ipynb``:

    uv run python src/scratch/assemble_notebook.py
"""

import ast
import json
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent
ORDER = ["llm.py", "tools.py", "report.py"]
OUT = SCRATCH / "_assembled.ipynb"


def split_imports(src):
    tree = ast.parse(src)
    import_segments = []
    import_lines = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_segments.append(ast.get_source_segment(src, node))
            import_lines.update(range(node.lineno, node.end_lineno + 1))
    lines = src.splitlines()
    body = "\n".join(
        line for i, line in enumerate(lines, 1) if i not in import_lines
    )
    return import_segments, body.strip("\n")


def code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def main():
    imports = []
    body_cells = []
    for name in ORDER:
        src = (SCRATCH / name).read_text()
        module_imports, body = split_imports(src)
        for imp in module_imports:
            if imp not in imports:
                imports.append(imp)
        header = f"# --- from src/scratch/{name} ---\n"
        body_cells.append(code_cell(header + body + "\n"))

    cells = [code_cell("\n".join(imports) + "\n"), *body_cells]
    notebook = {
        "cells": cells,
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    OUT.write_text(json.dumps(notebook, indent=1))
    print(
        f"Wrote {OUT} — {len(cells)} cells "
        f"({len(imports)} imports hoisted)."
    )


if __name__ == "__main__":
    main()
