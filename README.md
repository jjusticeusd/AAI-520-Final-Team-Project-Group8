# AAI-520 Final Team Project: Multi-Agent Financial Analysis System

**Group 8** - jjustice, pwang

An autonomous Investment Research Agent. Given a stock symbol, it plans its own
research steps, calls tools to gather market data and news, drafts an analysis,
critiques that draft, and refines it. Notes from each run are kept so later runs
on the same symbol start better informed.

Everything runs locally. No API keys, no paid services.

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
| Sentiment | BERT sentiment `pipeline` |
| Entity extraction | spaCy NER and PoS tagging |
| Retrieval | `all-MiniLM-L6-v2` embeddings in a FAISS index |
| Market data | Yahoo Finance via `yfinance` |
| Environment | Python 3.13, managed by `uv` |

## Setup

Requires macOS or Linux. Run once after cloning:

```bash
./init.sh
```

That installs `uv` if missing, then builds `.venv` from `pyproject.toml` and
`uv.lock` so every teammate gets identical versions.

The spaCy `en_core_web_sm` model is pinned in `pyproject.toml` and installed by
`uv sync`, so no separate download is needed. The NLTK data sets are downloaded
at runtime and are not covered by `uv sync`, so fetch them once:

```bash
uv run python -c "import nltk; [nltk.download(p) for p in ('punkt_tab','averaged_perceptron_tagger_eng','stopwords','wordnet')]"
```

The first notebook run also downloads the Phi-3-mini weights, roughly 7.6 GB,
into `~/.cache/huggingface`. That happens once.

## Running the notebook

Open `src/investment_research_agent.ipynb` and select the `./.venv/bin/python`
interpreter. In VS Code that is the interpreter picker at the top right.

For Jupyter Lab in the browser instead:

```bash
uv run --with jupyter jupyter lab
```

## Layout

```
src/
  investment_research_agent.ipynb   the graded deliverable
  scratch/                          per-person working files (.py) and tests, not submitted
data/                               cached yfinance responses, committed so runs are reproducible
schedule.md                         week-by-week task plan and deadlines
init.sh                             first-time environment setup
```

## Development

Component logic is built as plain `.py` files in `src/scratch/` so it can be unit
tested, then assembled into the notebook for submission:

```bash
uv run pytest src/scratch/                       # unit tests (no model, no network)
uv run python src/scratch/smoke_llm.py           # manual LLM check (loads the model)
uv run python src/scratch/assemble_notebook.py   # emit paste-ready notebook cells
```

## Contributing

`schedule.md` holds the task plan, deadlines, and owners. Two rules matter:

- Develop in your own `src/scratch/` files. Only one person edits
  `investment_research_agent.ipynb` at a time, otherwise the JSON merge
  conflicts are unresolvable.
- Run **Restart and Clear All Outputs** before committing. Outputs are kept only
  on the final submission run.

Python follows PEP 8.

## News report adapter

`src/scratch/news_report_adapter.py` maps saved news-chain results into
the existing five-field `specialist_result()` contract without calling
the model.

Each finding preserves summary text, claim IDs, source metadata and URLs,
original claim evidence, and the news review status. This nested finding
format is proposed for integration review.

Run the offline tests from the repository root:

```bash
uv run python src/scratch/test_news_report_adapter.py
```

To map the saved news result, run this Python code from the repository root:

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, "src/scratch")

from news_report_adapter import news_result_to_specialist
from report import assemble_report

path = Path(
    "data/demo/"
    "news_migration_explicit_llm_20260925T184649_793929Z.json"
)
chain = json.loads(path.read_text(encoding="utf-8"))

news = news_result_to_specialist(chain)
report = assemble_report({"news": news})

print(json.dumps(report, indent=2, ensure_ascii=False))
```

Six offline tests passed. The saved-data mapping preserved all five
summary findings, their cited evidence and source URLs, and the original
limitations. Update timestamps remain labeled as source metadata rather
than event dates.

[Mapping evidence](data/demo/news_report_mapping_20260927T031800_884190Z.json)
also includes an assembly test with explicitly synthetic price and
financial sections. Real price/financial specialist integration and
downstream rendering remain untested. News results still require manual
review.
