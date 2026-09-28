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

Then download the spaCy and NLTK models, which are not Python packages and are
not covered by `uv sync`:

```bash
uv run python -m spacy download en_core_web_sm
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
  scratch/                          per-person working notebooks, not submitted
data/                               cached yfinance responses, committed so runs are reproducible
  demo/                             fixed news test inputs, outputs, and review records
schedule.md                         week-by-week task plan and deadlines
init.sh                             first-time environment setup
```

## Contributing

`schedule.md` holds the task plan, deadlines, and owners. Two rules matter:

- Develop in your own `src/scratch/` notebook. Only one person edits
  `investment_research_agent.ipynb` at a time, otherwise the JSON merge
  conflicts are unresolvable.
- Run **Restart and Clear All Outputs** before committing. Outputs are kept only
  on the final submission run.

Python follows PEP 8.

## News baseline

The five-article Colab baseline is available in
[Phi3_Colab_Benchmark_AAPL_v3.ipynb](src/scratch/Phi3_Colab_Benchmark_AAPL_v3.ipynb).

Saved files:
- [Input snapshot](data/demo/aapl_news_snapshot_01.json)
- [Run results](data/demo/news_chain_results.json)
- [Review worksheet](data/demo/manual_review.csv)

To reproduce:
1. Open the notebook in a fresh Colab GPU runtime. Run sections 1–2,
   then section 8.
2. Upload the input snapshot to
   `/content/pwang_news/aapl_news_snapshot_01.json` before running section 9.
3. Run sections 9–12 with `RUN_LIMIT = 5`.
4. Run section 13 to download results. Keep new outputs separate from
   the saved baseline and clear notebook outputs before committing.

The inputs are Apple Newsroom summaries. Results remain
`needs_manual_review`; known omissions and validation details are
recorded in the saved results and review worksheet.
