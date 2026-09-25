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

## News baseline (Peng, Google Colab)

The news prototype was tested separately in
`Phi3_Colab_Benchmark_AAPL_v3.ipynb` on September 22, 2026. The workflow is
cleaning, classification, evidence-linked extraction, and summarization.
Integration into the repository notebook and connection to `data/AAPL_news.json`
are pending.

### Saved evidence

- [Input snapshot](data/demo/aapl_news_snapshot_01.json): five fixed AAPL news summaries, source metadata, and a records hash.
- [Run results](data/demo/news_chain_results.json): prompts, raw responses, claims, citations, validation checks, environment, and timings.
- [Review worksheet](data/demo/manual_review.csv): support checks, omissions, and review status.

The run produced 14 claims across 11 model calls: five classifications, five
extractions, and one summary. Raw strict-JSON compliance was **0/11**. After
removing complete Markdown code fences, **11/11** responses passed schema
validation. The recorded run status is `needs_manual_review`.

Total model generation time was **57.30 seconds**, excluding loading and other
overhead, on a Colab A100-SXM4-40GB with CUDA, bfloat16, and no quantization.
The earlier 300-token benchmark had a median of **10.55 seconds (28.44 tokens/s)**
across three runs. Full model revision and environment details are in the result
JSON; these measurements apply to the tested prompts and environment.

### Reproduce the Colab test

These steps require the separate experimental notebook named above.

1. Open it in a fresh Colab GPU runtime. Run sections 1-2 for dependencies and environment setup, then section 8 for news input helpers.
2. Create `/content/pwang_news/` in Colab's Files panel and upload the saved snapshot there as `aapl_news_snapshot_01.json` before running section 9.
3. Run sections 9-12 with `RUN_LIMIT = 5`. Section 9 validates and reuses the snapshot; without it, the code fetches the current feed instead.
4. Run section 13 to download the results ZIP. Keep new run outputs separate from this baseline. Notebook outputs should be cleared before committing code, as required above; selected evidence is retained in `data/demo/`.

### Limits and next integration step

- All five inputs are Apple Newsroom summaries (`text_type="summary"`), not full articles. Company-source bias and limited coverage remain; facts were not independently verified.
- `published_at` is unknown (`null`). `updated_at` is an update timestamp, not a publication or event date.
- Music Hall extraction and summary omit the opening event. Product-lineup extraction omits AirPods 5; its summary omits Apple Watch and AirPods and includes Watch claim IDs without describing Watch.
- Schema validity and resolvable citations do not establish factual support or completeness. This run does not evaluate the full multi-agent, evaluator-optimizer, or memory workflows.

Next, adapt the nested records in `data/AAPL_news.json` to the news input format
and check relevance before extraction. Develop in `src/scratch/` and agree on
`run_news_chain(records, llm=...)` input/output fields before integrating into the
shared notebook under the one-editor rule.
