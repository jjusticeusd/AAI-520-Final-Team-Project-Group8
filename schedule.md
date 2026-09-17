# AAI-520 Final Team Project: Schedule and Task Plan

**Group 8** - jjustice, pwang

**Team meeting: Wednesdays 7:00 PM, Zoom (recurring).**

Week-by-week tasks for the Multi-Agent Financial Analysis System. Each task
links to the requirement it satisfies. Check boxes as work lands. Owners are
assigned at the weekly meeting.

---

## Hard Deadlines

Times in PDT. Canvas stores them in UTC.

| Date | Deliverable | Who submits |
| --- | --- | --- |
| Mon Sep 21, 11:59 PM | Module 3 Check-In (5 pts) | external tool |
| Mon Sep 28, 11:59 PM | Module 4 Check-In (5 pts) | external tool |
| Mon Sep 28, 11:59 PM | Team Assignment 4.2: Project Status Update Form (10 pts) | one member |
| Mon Oct 5, 11:59 PM | Module 5 Check-In (5 pts) | external tool |
| Mon Oct 12, 11:59 PM | Module 6 Check-In (5 pts) | external tool |
| Mon Oct 19, 11:59 PM | **Final Code Notebook as PDF** (355 pts) | one member |
| Mon Oct 19, 11:59 PM | Assignment 7.1: Peer Evaluation Form (45 pts) | each member individually |

**No extensions are given. Work submitted after Oct 19 is not graded.**

The four check-ins are worth 5 points each, 20 points total. They are graded,
not optional progress notes.

---

## Locked Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| LLM runtime | Hugging Face `transformers`, local | Matches the Module 4 and 6 labs. No API key, no cost, reproducible from a clean checkout. |
| Primary model | `microsoft/Phi-3-mini-4k-instruct` | Module 6 lab. Not gated, so no Hugging Face login. |
| Fallback model | `meta-llama/Llama-3.2-1B-Instruct` | Module 6 lab. Faster, weaker. Gated: needs `huggingface_hub.login()`. |
| Embeddings | `all-MiniLM-L6-v2` + FAISS | Module 4 lab retrieval stack. |
| Data source | Yahoo Finance via `yfinance`, only | Prices, financials, and news from one API. Recommended by the assignment. Responses cached to `data/`. |
| Code layout | Single notebook in `src/` | Matches the Module 7 lab shape. |
| Agent scope | One ticker per run | Demoed across a small watchlist to show memory improving later runs. |

---

## Repository Layout

```
src/
  investment_research_agent.ipynb   # the graded deliverable
  scratch/                          # per-person working notebooks, not submitted
data/                               # cached yfinance responses (committed); memory.json (ignored)
schedule.md
README.md
pyproject.toml
init.sh
```

### Notebook merge rule

Two people editing one `.ipynb` produces unresolvable JSON merge conflicts.

1. Develop your piece in `src/scratch/<name>_<topic>.ipynb`.
2. Integrate into `investment_research_agent.ipynb` only at the weekly
   integration point, and only one person touches it at a time.
3. Run **Restart and Clear All Outputs** before every commit during development.
   Outputs are committed only on the final run.
4. Announce before you edit the main notebook.

---

## Project Requirements

From the assignment, so tasks can link directly to what they score.

### Agent Functions (33.8%, 120 pts)

Build an autonomous Investment Research Agent that:

#### AF1: Plans
Plans its research steps for a given stock symbol.

#### AF2: Uses Tools
Uses tools dynamically (APIs, datasets, retrieval).

#### AF3: Self-Reflects
Self-reflects to assess the quality of its output.

#### AF4: Learns
Learns across runs, keeping brief memories or notes to improve future analyses.

Full marks require all four implemented *and demonstrated* in the notebook.
Each missing function drops a full rubric band.

### Workflow Patterns (33.8%, 120 pts)

#### WP1: Prompt Chaining
Ingest News -> Preprocess -> Classify -> Extract -> Summarize.

#### WP2: Routing
Direct content to the right specialist (earnings, news, or market analyzers).

#### WP3: Evaluator-Optimizer
Generate analysis -> evaluate quality -> refine using feedback.

All three must be implemented and demonstrated.

### Code (32.4%, 115 pts)

#### CD1: Readable Notebook
Submitted as PDF (preferred) or HTML. Readable and well structured.

#### CD2: GitHub Link
The notebook must include the team's GitHub repository link, and the repo must
be consistent with the notebook.

#### CD3: Comments and Visualizations
Notebook comments must explain Agent Design and Workflows, Agent Functions and
Capabilities, and Evaluation and Iteration. Relevant visualizations required.
PEP 8 style. README required in the repo.

---

## How the Modules Map to the Build

The WP1 prompt chain is the course syllabus in order. Most pieces are reused.

| Chain step | Module | Reuse |
| --- | --- | --- |
| Ingest | - | `yfinance` prices, financials, news |
| Preprocess | 1 | tokenize, normalize, stopwords |
| Classify | 3 | BERT sentiment via HF `pipeline` |
| Extract | 2 | NER and PoS for companies, people, money, dates |
| Summarize | 4, 5 | local LLM with an engineered prompt |
| Retrieval tool | 4, 6 | FAISS + MiniLM embeddings, RAG query |
| Orchestration | 7 | `Agent` base class, workflow patterns |

---

## Week 1: Sep 16 - Sep 22 (Module 3 week)

Goal: repo is workable, both members can run a local LLM, data source proven.

| # | Task | Requirement | Owner |
| --- | --- | --- | --- |
| 1.1 | Assign owners for all remaining weeks | - |  |
| 1.2 | Add `transformers`, `torch`, `yfinance`, `faiss-cpu`, `sentence-transformers`, `nltk`, `spacy`, `pandas`, `matplotlib` to `pyproject.toml`; `uv sync` | CD1 |  |
| 1.3 | Write `README.md`: project summary, setup steps, how to run the notebook | CD2, CD3 |  |
| 1.4 | Confirm `.gitignore` excludes `.venv/`, `data/`, `.ipynb_checkpoints` | CD1 |  |
| 1.5 | Load Phi-3-mini and time one 300-token generation on each machine. Record the timings here | AF1 |  |
| 1.6 | Pull prices, financials, and news for one ticker via `yfinance`; confirm available fields; cache responses to `data/` | AF2 |  |
| 1.7 | Pick the demo watchlist (3 tickers, ideally with recent earnings) | - |  |
| 1.8 | Post Module 3 check-in | - |  |

**1.5 result (jjustice, Apple silicon):** Phi-3-mini on MPS with bfloat16 runs
at 15.3 tokens/sec, about 20 seconds for a 300-token generation. Model load is
5 seconds once weights are cached, 77 seconds on the first cold load. That is
fast enough for the Evaluator-Optimizer loop, so Phi-3-mini stays the primary
model and the Llama-3.2-1B fallback is not needed. Load with
`dtype=torch.bfloat16` and `.to("mps")`; the CPU float32 default is far slower.

Record pwang's timing here too. If a machine has no MPS and comes in above
roughly 60 seconds per call, that machine should use the fallback locally.

**transformers 5.x note:** `uv sync` resolves transformers 5.17, one major
version past the course labs. `apply_chat_template(..., return_tensors="pt")`
now returns a `BatchEncoding`, not a tensor, so lab code calling
`model.generate(ids, ...)` fails. Use `return_dict=True` and `generate(**enc)`.
Expect similar small breakages when porting other lab snippets.

---

## Week 2: Sep 23 - Sep 29 (Module 4 week)

Goal: the prompt chain runs end to end. Status form submitted.

| # | Task | Requirement | Owner |
| --- | --- | --- | --- |
| 2.1 | `llm(prompt) -> str` helper wrapping the HF pipeline, with temperature and max-token settings in one place | AF1 |  |
| 2.2 | Ingest step: fetch news for a ticker, return a list of article dicts | WP1 |  |
| 2.3 | Preprocess step: port Module 1 cleaning and tokenization | WP1 |  |
| 2.4 | Classify step: Module 3 BERT sentiment pipeline over headlines | WP1 |  |
| 2.5 | Extract step: Module 2 NER and PoS for companies, people, money, dates | WP1 |  |
| 2.6 | Summarize step: LLM prompt that narrates only the extracted facts | WP1 |  |
| 2.7 | Wire 2.2 through 2.6 into one `run_chain(ticker)` function and demo it | **WP1 done** |  |
| 2.8 | **Fill and submit Team Assignment 4.2 Status Update Form** | - |  |
| 2.9 | Post Module 4 check-in | - |  |

**Milestone: WP1 (Prompt Chaining) complete. Due Mon Sep 28.**

Extracted values from 2.5 are deterministic. Pass them into the summarize prompt
rather than letting the model produce figures on its own. Every number in the
summary should then be traceable to the extracted data, which doubles as a
grounding check in Week 4.

---

## Week 3: Sep 30 - Oct 6 (Module 5 week)

Goal: the agent plans, routes, and selects its own tools.

| # | Task | Requirement | Owner |
| --- | --- | --- | --- |
| 3.1 | Planner prompt: given a ticker, emit a JSON list of research steps. Few-shot, strict output format | **AF1** |  |
| 3.2 | Plan parser with a fallback to a default step list when the model returns malformed JSON | AF1 |  |
| 3.3 | Tool registry: dict of name -> function (`get_prices`, `get_news`, `get_financials`, `rag_query`) | **AF2** |  |
| 3.4 | Tool-selection prompt: LLM returns a tool name plus arguments; driver looks it up and calls it | AF2 |  |
| 3.5 | Router: classify input as earnings / news / market-data, dispatch to the matching specialist | **WP2** |  |
| 3.6 | Three specialist prompts: earnings analyzer, news analyzer, market analyzer | WP2 |  |
| 3.7 | Run trace: log every plan step, tool call, and routing decision | CD3 |  |
| 3.8 | Post Module 5 check-in | - |  |

**Milestone: AF1, AF2, WP2 complete.**

Cap the plan at a fixed number of steps. Uncapped agent loops are the standard
failure mode.

---

## Week 4: Oct 7 - Oct 13 (Module 6 week)

Goal: reflection loop and cross-run memory. This is the half of the grade that
is easiest to underbuild.

| # | Task | Requirement | Owner |
| --- | --- | --- | --- |
| 4.1 | RAG retrieval tool: chunk cached news and financials, embed with MiniLM, index in FAISS, expose `rag_query` | AF2 |  |
| 4.2 | Evaluator prompt: score a draft 1-5 on specificity, use of numbers, and coverage. Return JSON with score and feedback | **AF3** |  |
| 4.3 | Grounding check: assert every figure in the summary appears in the extracted facts; feed violations to the evaluator | AF3 |  |
| 4.4 | Optimizer loop: `while score < threshold and attempts < 3`, regenerate with evaluator feedback appended | **WP3** |  |
| 4.5 | Memory store: append per-ticker notes to `data/memory.json`, load into the planner and summarize prompts on the next run | **AF4** |  |
| 4.6 | Demonstrate AF4: run the same ticker twice, show the second run using notes from the first | AF4 |  |
| 4.7 | Visualization: score-per-iteration chart showing the optimizer loop improving output | CD3 |  |
| 4.8 | Visualization: workflow diagram of the agent architecture | CD3 |  |
| 4.9 | Post Module 6 check-in | - |  |

**Milestone: AF3, AF4, WP3 complete. All seven graded requirements implemented.**

Keep the before-and-after drafts from 4.4 in the notebook. The visible
improvement between iterations is the evidence that WP3 works.

---

## Week 5: Oct 14 - Oct 19 (Module 7 week) - FINAL

Goal: integrate, document, export, submit. No new features after Oct 16.

| # | Task | Requirement | Owner |
| --- | --- | --- | --- |
| 5.1 | Merge all scratch notebooks into `src/investment_research_agent.ipynb` in final order | CD1 |  |
| 5.2 | Header cell: team names, date, title, AI-use disclosure | CD1 |  |
| 5.3 | Confirm the GitHub repo link in the notebook | **CD2** |  |
| 5.4 | Write the Agent Design and Workflows commentary | **CD3** |  |
| 5.5 | Write the Agent Functions and Capabilities commentary, naming where AF1-AF4 are demonstrated | **CD3** |  |
| 5.6 | Write the Evaluation and Iteration commentary | **CD3** |  |
| 5.7 | PEP 8 pass over all code cells | CD3 |  |
| 5.8 | Rubric self-check: walk AF1-AF4, WP1-WP3, CD1-CD3 and point at the cell demonstrating each | all |  |
| 5.9 | **Code freeze Fri Oct 16.** Full clean run top to bottom, outputs committed | CD1 |  |
| 5.10 | Export to PDF. Read it end to end for cut-off cells and unreadable output | CD1 |  |
| 5.11 | Verify commit history shows contribution from both members | - |  |
| 5.12 | **Submit the PDF to Canvas** | - |  |
| 5.13 | **Each member submits the Peer Evaluation Form separately** | - |  |
| 5.14 | Post Module 7 check-in and Discussion 7.1 | - |  |
| 5.15 | Final Assessment: Course Knowledge Quiz | - |  |

**Milestone: submitted by Mon Oct 19, 11:59 PM PDT.**

---

## Risks

| Risk | Mitigation |
| --- | --- |
| Local model too slow to iterate on | Timed in 1.5. Fall back to Llama-3.2-1B. Cache LLM responses during development. |
| Small model returns malformed JSON | Strict few-shot prompts plus a parser fallback (3.2). A parse failure must not kill a run. |
| Notebook merge conflicts | Scratch notebooks plus the one-owner-at-a-time integration rule. |
| Optimizer loop never converges | Hard cap of 3 attempts, accept the best-scoring draft. |
| Uneven contribution affects individual grades | Team members may receive different grades. Commit history is the evidence; both members commit weekly. |
| PDF export mangles long outputs | Truncate verbose prints before the final run. Export and read the PDF on Oct 16, not Oct 19. |

---

## Cadence

Weekly engagement is required by the assignment.

- Zoom sync every Wednesday at 7:00 PM
- Both members commit something every week
- Post the module check-in every week, even if progress was small
