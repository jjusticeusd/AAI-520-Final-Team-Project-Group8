# Multi-Agent Financial Analysis System

This project is a part of the AAI-520 course in the Applied Artificial
Intelligence Program at the University of San Diego (USD).

**Project Status: Completed**

## Installation

Requires macOS or Linux, and Apple silicon (MPS) or a CUDA GPU; Phi-3-mini is
too slow on CPU.

```bash
git clone https://github.com/jjusticeusd/AAI-520-Final-Team-Project-Group8.git
cd AAI-520-Final-Team-Project-Group8
./init.sh
```

`init.sh` installs `uv` if missing, then builds `.venv` from `pyproject.toml`
and `uv.lock` so everyone gets identical versions. The first run downloads the
Phi-3-mini weights, roughly 7.6 GB, into `~/.cache/huggingface`. Optionally put
a Hugging Face token in `.env` as `HF_TOKEN=...` (gitignored).

Open `src/investment_research_agent.ipynb`, select the `./.venv/bin/python`
interpreter (or run `uv run --with jupyter jupyter lab`), and run all cells. A
full run takes about 15-20 minutes on Apple silicon and writes agent lessons to
`data/memory.json`. Export the executed notebook to HTML:

```bash
uv run --with nbconvert jupyter nbconvert --to html src/investment_research_agent.ipynb
```

## Project Intro/Objective

The main purpose of this project is to build an autonomous investment research
agent: given a stock symbol, it plans its own research, calls tools for prices,
financials and news, routes the results to specialist analysts, drafts a
research note, critiques and revises it, and keeps lessons that improve its next
run. It demonstrates the four agent functions (plans, uses tools dynamically,
self-reflects, learns across runs) and three workflow patterns (prompt
chaining, routing, evaluator-optimizer) from the course, running entirely on a
local open model with no paid services.

## Partner(s)/Contributor(s)

- Jason Justice
- Peng Wang

## Methods Used

- Natural Language Processing
- Large Language Models and prompt engineering (zero-shot, few-shot, structured
  JSON output)
- Retrieval-augmented generation (sentence embeddings, cosine similarity)
- Multi-agent systems (planning, tool use, routing, orchestrator-workers,
  evaluator-optimizer, memory)
- Data visualization

## Technologies

- Python 3.13, managed by `uv`
- Hugging Face `transformers` with `microsoft/Phi-3-mini-4k-instruct`
- `sentence-transformers` with `all-MiniLM-L6-v2`
- `yfinance`
- `pandas`, `matplotlib`
- Jupyter

## Project Description

The agent's workflow has these steps:
- **Plan and fetch:** a Planner chooses tool calls and their arguments, a Tool executor runs them, and the Planner reviews the results and may add follow-up calls.
- **Analyze:** a Router sends each result to a market, earnings or news analyst. The news analyst runs a prompt chain: ingest, preprocess, classify, extract, summarize.
- **Write and review:** a Writer drafts the research note, and a Critic scores it against a rubric, backed by code checks for invented numbers, missing headings, repeated sentences and copied reviewer comments. The Writer revises up to three drafts.
- **Learn:** lessons from the review are saved and used by the next run's Planner.

The notebook runs AAPL twice (to show learning across runs), then TSLA with live data, then a labeled weak-draft example of the revision loop.

Data comes from Yahoo Finance through `yfinance`:

| Data | Source call | Size per ticker | Fields |
| --- | --- | --- | --- |
| Daily prices | `Ticker.history` | 251 trading days (one year) | Open, High, Low, Close, Volume, Dividends, Stock Splits |
| Quarterly income statement | `Ticker.quarterly_financials` | 33-47 line items x 5 quarters | e.g. Total Revenue, Gross Profit, Operating Income, Net Income, Diluted EPS |
| News | `Ticker.news` (cached), `Search.news` (live) | 10 cached articles | id, title, summary, publisher, publish date |

Snapshots for AAPL, MSFT and NVDA, taken Sep 16-17, 2026, are committed in `data/` so the notebook's outputs are reproducible. Any other ticker falls through to the live API.

Questions explored:
- Can a small local model plan research, choose tools and arguments, and route content reliably?
- Does a critique-and-revise loop improve a draft?
- Do lessons from one run measurably change the next run's plan?

Challenges:
- **The model's output needs checking.** Phi-3-mini sometimes returns malformed JSON and needs validation and retries. It also marks loosely related articles as relevant, so preprocessing keeps only articles that mention the company.
- **Yahoo's data is thin.** Its per-ticker news is often only loosely about the company, and the live search API returns headlines only.
- **Meaning errors get through.** Citations and passing review scores do not prove the content is accurate; for example, a claim can reverse the meaning of the headline it quotes. These are documented in the supplemental report.

## Repository Layout

```
src/
  investment_research_agent.ipynb   the graded deliverable
  investment_research_agent.html    executed export of the notebook
  scratch/                          early foundation modules, tests, and pwang's news prototype
data/                               cached yfinance responses, committed so runs are reproducible
  demo/                             pwang's news prototype inputs, outputs, and review records
  memory.json                       agent lessons across runs (runtime, gitignored)
schedule.md                         task plan, status, and deadlines
init.sh                             first-time environment setup
```

Development checks: `uv run pytest src/scratch/` runs the scratch module tests,
and `./check_pep8.sh` runs the PEP 8 check (also run in CI).

## License

This project is licensed under the MIT License; see [LICENSE](LICENSE).

## Acknowledgments

Thanks to the AAI-520 instructors for the course material this project builds
on, especially the Module 7 lab and presentation on agentic AI and the
Anthropic readings on building effective agents.
