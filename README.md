# AAI-520 Final Team Project: Multi-Agent Financial Analysis System

**Group 8** - jjustice, pwang

An autonomous Investment Research Agent. Given a stock symbol, it plans its own
research steps, calls tools to gather market data and news, drafts an analysis,
critiques that draft, and refines it. Notes from each run are kept so later runs
on the same symbol start better informed.

Everything runs locally. No paid services.

## What it demonstrates

**Agent functions**

- **Plans** its research steps for a given stock symbol
- **Uses tools** dynamically: prices, financials, news, and retrieval
- **Self-reflects** by scoring its own draft and acting on the critique
- **Learns** across runs by keeping short per-symbol notes

**Workflow patterns**

- **Prompt chaining**: Ingest News -> Preprocess -> Classify -> Extract -> Summarize
- **Routing**: send content to an earnings, news, or market specialist
- **Evaluator-Optimizer**: generate, evaluate, refine on feedback

## Stack

| Piece | Choice |
| --- | --- |
| Language model | `microsoft/Phi-3-mini-4k-instruct`, run locally via Hugging Face `transformers` |
| Retrieval | `all-MiniLM-L6-v2` embeddings via `sentence-transformers` |
| Market data and news | Yahoo Finance via `yfinance` |
| Metrics and plots | `pandas`, `matplotlib` |
| Environment | Python 3.13, managed by `uv` |

Phi-3-mini needs Apple silicon (MPS) or a CUDA GPU; CPU is too slow to use.

## Setup

Requires macOS or Linux. Run once after cloning:

```bash
./init.sh
```

That installs `uv` if missing, then builds `.venv` from `pyproject.toml` and
`uv.lock` so every teammate gets identical versions.

The first run downloads the Phi-3-mini weights, roughly 7.6 GB, into
`~/.cache/huggingface`. That happens once. Optionally put a Hugging Face token
in `.env` as `HF_TOKEN=...` (gitignored) and pass `--env-file .env` to
`uv run` to avoid unauthenticated-download warnings.

## Running

The agent on one ticker, and the full demonstration of every requirement:

```bash
uv run --env-file .env python src/scratch/agent.py AAPL
uv run --env-file .env python src/scratch/demo.py    # about 15-20 min
```

`demo.py` runs AAPL twice from fresh memory (learning across runs), then TSLA,
which has no local cache (live tool calls), plus a labeled weak-draft example of
the evaluator-optimizer loop. Plots are written to `evidence/`.

The notebook: open `src/investment_research_agent.ipynb` and select the
`./.venv/bin/python` interpreter, or run `uv run --with jupyter jupyter lab`.

## Layout

```
src/
  investment_research_agent.ipynb   the graded deliverable
  scratch/                          working .py modules and tests, assembled into the notebook
data/                               cached yfinance responses, committed so runs are reproducible
  demo/                             pwang's WP1 news prototype inputs, outputs, and review records
  memory.json                       agent lessons across runs (runtime, gitignored)
evidence/                           plots from demo runs
schedule.md                         task plan, status, and deadlines
init.sh                             first-time environment setup
```

## Development

```bash
uv run pytest src/scratch/     # unit tests (fake LLM, no network)
./check_pep8.sh                # PEP 8 check, also run in CI
```

`schedule.md` holds the task plan, deadlines, owners, and current status. Only
one person edits `investment_research_agent.ipynb` at a time; the JSON merge
conflicts are otherwise unresolvable. Run **Restart and Clear All Outputs**
before committing it, except for the final submission run.

pwang's original WP1 prototype (`news_pipeline.py`, `news_report_adapter.py`)
and the Colab benchmark notebook remain in `src/scratch/` for reference.
