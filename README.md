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

## News pipeline integration (Peng)

The news workflow is implemented in `src/scratch/news_pipeline.py` and
called through `report.run_news_chain(records, llm=None)`. It performs
ingestion, preprocessing, classification, extraction, and summarization.

### Run the pipeline

After completing the repository setup, run the following Python code
from the repository root:

```python
import sys

sys.path.insert(0, "src/scratch")

import llm as backend
from tools import get_news
from report import run_news_chain

records = get_news("AAPL")
result = run_news_chain(records, llm=backend.llm)

print(result["status"])
print(result["summary"])
```

The pipeline explicitly passes `temperature=0`, the evidence-only system
prompt, and `max_new_tokens=700` to the supplied LLM function.

For the current `get_news()` implementation, `retrieved_at=None` indicates
a cache hit; a populated timestamp indicates a live fetch. This convention
applies to records returned by that function. A separately loaded snapshot
is documented as `saved_snapshot`.

### Reproduce the five-article migration test

The following code uses the committed snapshot rather than fetching news.
Run it from the repository root in an environment with the required model
dependencies and sufficient GPU memory:

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, "src/scratch")

import llm as backend
from news_pipeline import digest
from report import run_news_chain

snapshot_path = Path("data/demo/aapl_news_snapshot_01.json")
snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

assert snapshot["records_sha256"] == digest(snapshot["records"])
assert snapshot["ticker"] == "AAPL"
assert len(snapshot["records"]) == 5

result = run_news_chain(snapshot["records"], llm=backend.llm)

print("Version:", result["pipeline_version"])
print("Status:", result["status"])
print("Claims:", len(result["claims"]))
print("Model calls:", len(result["trace"]))
print(result["summary"])
```

The top-level `summary` is a string. Structured summary bullets, claim
references, source URLs, and limitations are available in
`result["stages"]["summarize"]`. The `trace` contains prompts, raw responses,
generation settings, validation results, and errors.

Run the offline tests from the repository root:

```bash
python src/scratch/test_news_pipeline.py
```

These 15 tests use synthetic responses and require no model loading or
network access. They check software behavior, including the generation
parameters passed to the supplied LLM function.

### Recorded validation

The explicit-callback run was completed on September 25, 2026, using
Phi-3-mini-4k-instruct on a Google Colab NVIDIA A100-SXM4-40GB GPU with
CUDA and bfloat16.

- Pipeline version: `news_module_migration_v2`.
- Input: the original five-article AAPL snapshot.
- Model calls: 11; extracted claims: 14.
- Recorded call errors: 0; excluded inputs: 0.
- All 11 raw responses and the structured summary matched the original baseline.
- Raw strict-JSON compliance: 0/11.
- After removing Markdown code fences, schema validation passed for 11/11 responses.
- Final status: `needs_manual_review`.
- All 15 offline tests and a local PEP 8 check passed.
- The full repository test suite has not yet been verified for this change.

[Explicit-callback run evidence](data/demo/news_migration_explicit_llm_20260925T184649_793929Z.json)
includes model settings, environment details, and source-file hashes.
The original baseline files are retained separately.

### Known limitations

- All five inputs are Apple Newsroom summaries. This test checks migration
  behavior, not independent factual accuracy or source diversity.
- Existing omissions remain: the Music Hall opening event is missing from
  the extracted claims and summary; AirPods information is missing from
  extraction, and Watch information is missing from the final summary.
- Some summary citations are broader than necessary.
- Sentiment labels and dedicated company, metric, value, unit, and
  event-date/period fields are not yet implemented.
- Passing `llm.llm` directly does not use the default wrapper's context-length
  precheck. Long-input handling requires further validation.
- Mapping the news output into the common specialist-result format and
  integrating the final deliverable notebook remain pending.
- Successful schema validation does not establish factual correctness.
