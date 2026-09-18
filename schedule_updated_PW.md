# AAI-520 Final Team Project: Schedule and Task Plan

**Group 8** - jjustice, pwang

**Team meeting: Wednesdays 7:00 PM, Zoom (recurring).**

Week-by-week tasks for the Multi-Agent Financial Analysis System. Each task
links to the requirement it satisfies. **[UPDATED] Owners are assigned below; review progress and rebalance effort at each weekly meeting.**

> **Revision guide:** **[ADDED]** marks new sections; **[UPDATED]** marks revised sections or notes. **New or modified wording and owner assignments are bold.** Existing emphasis is retained. The repository tree is marked as a revised block because bold does not render inside code fences.

## **[ADDED] Review Against the Assignment and Rubric**

**The original schedule covers all four agent functions, all three workflow patterns, and the main code deliverables. It broadly meets the requirements as a planning document. It cannot establish that the finished project meets the rubric: the submitted, executed notebook must demonstrate each behavior.**

**This revision adds explicit ownership, observable completion criteria, connected workflows, and final submission checks. The rubric totals 355 points: Agent Functions 120, Workflow Patterns 120, and Code 115. Implementation choices and internal quality targets below are team decisions, not additional instructor requirements.**

---

## Hard Deadlines

**[UPDATED] The calendar dates, check-ins, and additional assignment points below are retained from the original schedule, but are not independently confirmed by the supplied assignment or screenshot. Verify them in Canvas. The supplied instructions confirm the Module 4 status update, Module 7 final notebook, and separate Module 7 peer evaluations. Times below are the original schedule's PDT times; verify the Canvas display timezone.**

| Date | Deliverable | Who submits |
| --- | --- | --- |
| Mon Sep 21, 11:59 PM | Module 3 Check-In (5 pts) | **Each member checks the external-tool instructions** |
| Mon Sep 28, 11:59 PM | Module 4 Check-In (5 pts) | **Each member checks the external-tool instructions** |
| Mon Sep 28, 11:59 PM | Team Assignment 4.2: Project Status Update Form (10 pts) | **jjustice, proposed team representative; both prepare it** |
| Mon Oct 5, 11:59 PM | Module 5 Check-In (5 pts) | **Each member checks the external-tool instructions** |
| Mon Oct 12, 11:59 PM | Module 6 Check-In (5 pts) | **Each member checks the external-tool instructions** |
| Mon Oct 19, 11:59 PM | **Final Code Notebook as PDF (preferred) or HTML (355 pts)** | **jjustice, proposed team representative; both verify it** |
| Mon Oct 19, 11:59 PM | Assignment 7.1: Peer Evaluation Form (45 pts) | each member individually |

**[UPDATED] No extensions are given; final projects submitted after the actual Canvas deadline will not be graded. Confirm the original schedule's four 5-point check-ins and their submission rules in Canvas; those details are not established by the provided final-project rubric.**

**[ADDED] Confirm the Module 1 Teammate Survey and Module 2 group contact steps are complete. Weekly work windows below extend through Tuesday, but Monday deliverables must be completed before their Monday deadlines.**

---

## **[ADDED] Responsibilities and Required Evidence**

**Peng Wang (pwang) owns self-reflection, prompt chaining, evaluator–optimizer, and the news implementation. The remaining lead assignments below are proposed for jjustice. Both members contribute code, explanations, review, and weekly progress. Ownership means implementing and documenting the component, not only describing its design.**

| Area | Lead | Evidence to show in the executed notebook |
| --- | --- | --- |
| **AF1: Plans** | **jjustice** | **Ticker-specific generated plan and a trace linking research actions to that plan.** |
| **AF2: Uses tools dynamically** | **jjustice; pwang supplies the news tool** | **Chosen tool, validated arguments, returned result, and examples of choices responding to different research needs or results.** |
| **AF3: Self-reflects** | **pwang** | **Draft plus a structured critique identifying supported claims, unsupported claims, missing coverage, and limitations.** |
| **AF4: Learns across runs** | **jjustice; pwang supplies useful critique notes** | **A saved lesson retrieved on a later run and a visible change in the plan, tool choice, or analysis caused by that lesson.** |
| **WP1: Prompt chaining** | **pwang** | **Ingest → Preprocess → Classify → Extract → Summarize, with intermediate outputs passed between stages and displayed.** |
| **WP2: Routing** | **jjustice; pwang supplies the news specialist** | **Executed earnings, news, and market examples showing route decisions and the selected specialist's output.** |
| **WP3: Evaluator–optimizer** | **pwang; jjustice integrates it** | **Initial draft → actionable feedback → revised draft → re-evaluation, with a bounded stopping condition.** |
| **News code and news commentary** | **pwang** | **Ingestion, source-preserving preprocessing, classification, extraction, summarization, and news examples.** |
| **Market/earnings code and system integration** | **jjustice** | **Price/financial tools, specialists, planner, router, memory, and an integrated ticker-to-report run.** |
| **Code quality and final submission** | **Both; jjustice coordinates integration/export** | **Readable PDF/HTML, useful comments/Markdown, relevant visualizations, working GitHub link, README, PEP 8, and contributions from both members.** |

**AF3 and WP3 may share the evaluator implementation. Document them separately: AF3 demonstrates assessment; WP3 demonstrates an actual feedback-driven revision. Peng's evaluator should support the combined research report as well as the news summary. jjustice provides market/earnings evidence in the agreed format.**

---

## **[UPDATED] Working Technical Decisions**

**These are project choices, not course mandates. Keep the original local-model approach, and prioritize the seven required behaviors before optional features.**

| Decision | Choice | Rationale |
| --- | --- | --- |
| LLM runtime | Hugging Face `transformers`, local | **Retain the planned runtime; verify installation and generation on the actual machines and record tested versions.** |
| Primary model | `microsoft/Phi-3-mini-4k-instruct` | **Retain the original model choice, subject to the team's speed and structured-output checks.** |
| Fallback model | `meta-llama/Llama-3.2-1B-Instruct` | **Original fallback candidate; verify access and output quality before depending on it. Use an accessible tested alternative if needed.** |
| Embeddings | **Optional: `all-MiniLM-L6-v2` + FAISS** | **Retrieval is useful but not required when APIs/datasets already demonstrate dynamic tool use.** |
| Data source | **Yahoo Finance via `yfinance`, primary** | **Verify available prices, financials, and news fields. Preserve attributed demo snapshots; if news is unavailable, use a documented cached snapshot or an assignment-listed news source.** |
| Code layout | Single notebook in `src/` | **One integrated graded notebook, with per-person development notebooks and regular integration.** |
| Agent scope | One ticker per run | **One ticker is sufficient for the core demonstration; the planned three-ticker watchlist is a robustness check. Demonstrate memory separately using the same ticker across two runs.** |

---

## Repository Layout

**[UPDATED] Track small, attributed demo snapshots and selected evidence; ignore runtime cache and mutable memory. Do not ignore the entire `data/` directory.**

```text
src/
  investment_research_agent.ipynb   # integrated notebook; executed for submission
  scratch/                          # per-person development notebooks
data/
  demo/                             # small, permitted, attributed snapshots; tracked
  cache/                            # runtime API cache; ignored
  memory.json                       # runtime learning notes; ignored
evidence/                           # selected run traces and memory-demo records; tracked
schedule.md
README.md
pyproject.toml
uv.lock                             # tested dependency versions; tracked
init.sh
```

### Notebook merge rule

**[UPDATED] Concurrent edits to `.ipynb` files can cause difficult merge conflicts.**

1. Develop your piece in `src/scratch/<name>_<topic>.ipynb`.
2. Integrate into `investment_research_agent.ipynb` only at the weekly
   integration point, and only one person touches it at a time.
3. **[UPDATED] Clear bulky scratch outputs as needed, but preserve selected integration evidence. Before final export, restart the kernel, run all cells, and commit the executed notebook and matching code.**
4. Announce before you edit the main notebook.

### **[ADDED] Shared Interfaces and Integration Contract**

- **News records retain `article_id`, ticker/company, source, URL or dataset reference, publication/retrieval times when available, original text, cleaned text, and `text_type` (headline, summary, or full article). Record unavailable fields explicitly.**
- **`run_news_chain(records)` returns stage outputs, source-linked extracted claims, the news summary, and a trace. jjustice's router invokes this same news specialist.**
- **Every specialist returns a common result structure: findings, supporting source IDs, relevant dates/units, missing data, and limitations. The report assembler preserves those source links.**
- **`evaluate_report(draft, evidence)` returns criterion scores, specific issues, feedback, and pass/fail; `refine_report(draft, feedback, evidence)` returns a revised draft. pwang owns both behaviors; jjustice supplies orchestration and specialist evidence.**
- **Agree on these interfaces in Week 1; integrate the first news chain in Week 2. Emit concise decision records and observable results, rather than relying on an architecture diagram alone.**

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

**[UPDATED] For this rubric category: 120 points requires all four functions implemented and successfully demonstrated; 90 means all implemented with minor details missing; 60 means one function is not successfully implemented or demonstrated; 30 means more than one is missing; 0 is non-performance. These are category-level bands, not equal points per function.**

### Workflow Patterns (33.8%, 120 pts)

#### WP1: Prompt Chaining
Ingest News -> Preprocess -> Classify -> Extract -> Summarize.

#### WP2: Routing
Direct content to the right specialist (earnings, news, or market analyzers).

#### WP3: Evaluator-Optimizer
Generate analysis -> evaluate quality -> refine using feedback.

**[UPDATED] All three must be implemented and demonstrated for the 120-point band. The same 90/60/30/0 band logic applies to minor missing details, one missing workflow, more than one missing workflow, and non-performance. A static diagram or unexecuted function definition is insufficient evidence.**

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

**[ADDED] The 115-point band requires successful accomplishment of all requirements, a readable and well-structured document, useful commentary and relevant visualizations, and a viable GitHub link consistent with the notebook. Write Markdown explanations before major steps and interpretations after outputs. A supplemental PDF/Word report may provide the explanatory material, but never replaces the required notebook PDF/HTML.**

---

## How the Modules Map to the Build

**[UPDATED] Reuse applicable course techniques without making every earlier NLP technique mandatory. The module associations below follow the original plan and should be checked against the actual labs.**

| Chain step | Module | Reuse |
| --- | --- | --- |
| Ingest | - | **News records from the chosen source; prices/financials are separate tools** |
| Preprocess | 1 | **Whitespace/HTML cleanup and deduplication; preserve casing, negation, numbers, and source text** |
| Classify | 3 | **A classification prompt; BERT sentiment may provide an optional supporting comparison** |
| Extract | 2 | **A source-linked extraction prompt; spaCy NER/PoS may assist inspection** |
| Summarize | 4, 5 | **Local LLM consumes prior stage outputs and their evidence** |
| Retrieval tool | 4, 6 | **Optional FAISS + MiniLM retrieval after core requirements work** |
| Orchestration | 7 | **Role-specific agents, routing, bounded evaluation, and memory** |

**[ADDED] Make prompt chaining explicit: classification output feeds the extraction prompt; extracted claims and their evidence feed the summarization prompt. Ingestion and cleanup can be ordinary Python. Avoid relying on a fixed preprocessing pipeline with only one final prompted generation as the sole WP1 demonstration. Distinct specialist roles may share one underlying LLM.**

---

## Week 1: Sep 16 - Sep 22 (Module 3 week)

**[UPDATED] Goal: workable repo, tested model, verified data fields, agreed interfaces, and assigned owners.**

| # | Task | Requirement | Owner |
| --- | --- | --- | --- |
| 1.1 | **Review the ownership table and balance weekly effort; record issues and acceptance criteria** | **Groupwork** | **Both** |
| 1.2 | **Add core dependencies to `pyproject.toml`; `uv sync`; commit `uv.lock`. Add BERT/spaCy/retrieval dependencies only when used** | CD1 | **jjustice** |
| 1.3 | **Write README: project summary, both contributors, setup, data sources, model access, run/export steps, and current status** | CD2, CD3 | **jjustice; pwang adds news/evaluation details** |
| 1.4 | **Ignore `.venv/`, `data/cache/`, runtime `data/memory.json`, and `.ipynb_checkpoints`; track `data/demo/` and selected evidence** | CD1 | **jjustice** |
| 1.5 | **Time a 300-token generation on each machine; check one structured response and record environment/results** | **CD1; supports later AF1** | **Both** |
| 1.6 | **Verify price/financial fields and news fields for one ticker; retain source metadata and an attributed demo snapshot; record whether text is a headline, summary, or full article** | AF2 | **jjustice: prices/financials; pwang: news** |
| 1.7 | **Pick the demo ticker and optional three-ticker robustness watchlist** | **Demonstration scope** | **Both** |
| 1.8 | **Complete Module 3 check-in under the verified Canvas instructions, before Monday's deadline** | **Course activity; verify** | **Both** |
| **1.9** | **Agree on tool, specialist-output, evaluator, and memory-note interfaces; create one sample news record and report for integration** | **AF2, AF3, WP1–WP3** | **Both** |

**[UPDATED] Existing team-reported 1.5 result (jjustice, Apple silicon): Phi-3-mini on MPS with bfloat16 ran at 15.3 tokens/sec, approximately 20 seconds for 300 tokens; model load was 5 seconds with cached weights and 77 seconds on first load. Preserve this as a reported benchmark, not a guarantee for pwang's machine or all prompts.**

**Record pwang's timing and tested environment. If generation is too slow, use a tested accessible fallback and recheck analysis/JSON quality. Local speed alone does not establish evaluator quality.**

**[UPDATED] Existing compatibility observation: the original plan reports Transformers 5.17 and a chat-template mapping output requiring `generate(**enc)` with an explicit `return_dict=True`. Verify this against the installed version and actual model; retain the successful invocation in the notebook and pin the tested environment. Do not assume `uv sync` always resolves the same version.**

---

## Week 2: Sep 23 - Sep 29 (Module 4 week)

**[UPDATED] Goal: prompt chain runs end to end and is integrated; both members prepare the status form for the verified Module 4 deadline.**

| # | Task | Requirement | Owner |
| --- | --- | --- | --- |
| 2.1 | **Implement a shared `llm(prompt)` helper with generation settings and error handling in one place** | **CD1; supports AF1/WP1/WP3** | **jjustice** |
| 2.2 | **Ingest news into the agreed article schema; handle empty results and label cached-data runs** | WP1 | **pwang** |
| 2.3 | **Preprocess with cleanup/deduplication; retain original text, provenance, casing, negation, values, and units** | WP1 | **pwang** |
| 2.4 | **Classify each item using a prompt that returns content category and sentiment with article IDs; optional BERT comparison** | WP1 | **pwang** |
| 2.5 | **Extract structured claims using the classification output plus source text; retain company, metric, value/unit, date/period, source ID, and supporting spans when available** | WP1 | **pwang** |
| 2.6 | **Summarize the extracted claims using their evidence; include source references and explicitly identify missing information** | WP1 | **pwang** |
| 2.7 | **Wire all five stages together; display representative full inputs/intermediate outputs/final summary in the main notebook** | **WP1 acceptance check** | **pwang; jjustice reviews integration** |
| 2.8 | **Fill and submit Team Assignment 4.2 Status Update Form with actual progress, contributions, blockers, and next steps** | **Module 4 submission** | **Both prepare; jjustice submits** |
| 2.9 | **Complete Module 4 check-in under verified Canvas instructions** | **Course activity; verify** | **Both** |
| **2.10** | **Prepare price/financial tools and report-assembly scaffolding; integrate Peng's news output using the shared schema** | **AF2, WP2, CD1** | **jjustice** |

**[UPDATED] Target milestone: WP1 implemented and demonstrated; Module 4 status form submitted by the confirmed Monday deadline (original plan: Sep 28). Mark completion only after reviewing executed outputs.**

**[UPDATED] Extracted values are predictions, not guaranteed facts. Preserve supporting source spans and review representative claims. A number appearing somewhere in an article does not prove that it belongs to the right company, metric, unit, or reporting period. Calculated values must identify the source inputs and calculation.**

---

## Week 3: Sep 30 - Oct 6 (Module 5 week)

Goal: the agent plans, routes, and selects its own tools.

| # | Task | Requirement | Owner |
| --- | --- | --- | --- |
| 3.1 | **Planner prompt: ticker + research goal + available tools + relevant memory → bounded JSON research plan** | **AF1** | **jjustice** |
| 3.2 | **Validate the plan; log malformed output and any fallback. Demonstrate at least one successful generated plan; a fixed fallback alone does not prove planning** | AF1 | **jjustice** |
| 3.3 | **Tool registry with `get_prices`, `get_news`, `get_financials`; add `rag_query` only if implemented** | **AF2** | **jjustice; pwang supplies `get_news`** |
| 3.4 | **Choose tool names/arguments from the research need and available results; validate calls and display contrasting choices** | AF2 | **jjustice** |
| 3.5 | **Router dispatches content to earnings, news, or market specialists; record the selected route and result** | **WP2** | **jjustice** |
| 3.6 | **Implement earnings and market specialists; connect the existing news chain as the news specialist** | WP2 | **jjustice: earnings/market; pwang: news** |
| 3.7 | **Record plan steps, tool choices/arguments/results, routes, and source IDs; demonstrate all three specialist routes** | **AF1, AF2, WP2, CD3** | **jjustice; pwang reviews news trace** |
| 3.8 | **Complete Module 5 check-in under verified Canvas instructions** | **Course activity; verify** | **Both** |
| **3.9** | **Draft evaluator criteria and review several news outputs manually; identify a documented weakness for the refinement demonstration** | **AF3, WP3 preparation** | **pwang** |

**[UPDATED] Target milestone: AF1, AF2, and WP2 implemented and demonstrated in the integrated notebook. Log bounded steps, failures, and stopping reasons. A static sequence of all tools does not establish dynamic selection.**

---

## Week 4: Oct 7 - Oct 13 (Module 6 week)

**[UPDATED] Goal: complete self-reflection, feedback-driven refinement, and learning across runs. These support separate rubric requirements; the rubric does not assign a fixed independent score to each function.**

| # | Task | Requirement | Owner |
| --- | --- | --- | --- |
| 4.1 | **Optional RAG: implement MiniLM/FAISS retrieval only after the core tools and workflows are stable** | AF2 | **jjustice** |
| 4.2 | **Evaluator returns 1–5 criterion scores, specific evidence-linked issues, feedback, and pass/fail for grounding, relevance, coverage, uncertainty, and clarity** | **AF3** | **pwang** |
| 4.3 | **Check claims against source spans: company/metric/value/unit/period; flag unsupported claims and document calculations. Review a small sample manually** | AF3 | **pwang; jjustice supplies financial evidence** |
| 4.4 | **Refine the draft using evaluator feedback, then re-evaluate. Limit to three total drafts (initial + up to two revisions); record the stopping reason** | **WP3** | **pwang; jjustice integrates orchestration** |
| 4.5 | **Persist concise, source-aware lessons in `data/memory.json`; retrieve relevant lessons for later planning/drafting. Keep procedural lessons distinct from potentially stale financial facts** | **AF4** | **jjustice; pwang supplies reflection notes** |
| 4.6 | **Run the same ticker twice with the same source snapshot: show the stored lesson, later retrieval, and the specific action/output changed by it** | AF4 | **jjustice; pwang reviews evidence** |
| 4.7 | **Plot evaluation scores across actual iterations and show a before/after issue table; report plateaus or unresolved issues honestly** | CD3 | **pwang** |
| 4.8 | **Create the workflow diagram from the implemented system, including routing, the news chain, evaluator loop, and memory** | CD3 | **jjustice; pwang reviews owned components** |
| 4.9 | **Complete Module 6 check-in under verified Canvas instructions** | **Course activity; verify** | **Both** |

**[ADDED] Internal acceptance rule, not an instructor threshold: mean evaluator score at least 4/5, no known unsupported material claims, and any missing data disclosed. If the draft limit is reached without passing, return the best available draft with unresolved issues and `needs_review` status. Validate evaluator output so malformed scores do not silently pass.**

**[UPDATED] Target milestone: all four agent functions and all three workflows are implemented and demonstrated. Keep an initial draft, actionable critique, actual revision, and re-evaluation visible. If the first draft passes immediately, include a separate, clearly labeled refinement example with a documented weakness; do not invent scores or imply a seeded example occurred in a normal run.**

**[ADDED] Loading a memory file alone does not demonstrate learning. Explain the lesson's effect on the second run; if it does not help, report the limitation. A higher self-evaluation score alone does not prove factual improvement.**

---

## Week 5: Oct 14 - Oct 19 (Module 7 week) - FINAL

Goal: integrate, document, export, submit. No new features after Oct 16.

| # | Task | Requirement | Owner |
| --- | --- | --- | --- |
| 5.1 | **Finalize the already integrated notebook; arrange demonstrations in readable order** | CD1 | **jjustice; both review** |
| 5.2 | **Header: title, both team members, date, actual GitHub link, and contribution summary; add AI-use disclosure if required by course policy** | **CD1, CD2** | **Both** |
| 5.3 | **Verify the repository link works for the intended grader and points to code consistent with the submitted notebook** | **CD2** | **jjustice; pwang checks** |
| 5.4 | **Write Agent Design and Workflows commentary: news chain/evaluator loop and planning/routing/system diagram** | **CD3** | **pwang: WP1/WP3; jjustice: architecture/WP2** |
| 5.5 | **Write Agent Functions and Capabilities commentary; link each AF requirement to its actual demonstration heading** | **CD3** | **pwang: AF3; jjustice: AF1/AF2/AF4** |
| 5.6 | **Write Evaluation and Iteration commentary, including source checks, before/after evidence, memory results, and limitations** | **CD3** | **pwang leads; jjustice adds memory/tool results** |
| 5.7 | **PEP 8 review; ensure both members can follow setup and execute the notebook** | CD3 | **Both** |
| 5.8 | **Walk through the final evidence checklist below; fix missing implementation or demonstration** | all | **Both** |
| 5.9 | **Code freeze Fri Oct 16; restart and run all cells, commit outputs, and record the final commit used for export** | CD1 | **jjustice runs; pwang verifies owned sections** |
| 5.10 | **Export PDF (preferred) or HTML; inspect beginning to end for cut-off code, missing figures, truncated evidence, broken links, and unreadable text** | CD1 | **Both** |
| 5.11 | **Verify weekly contributions from both members through code, issues/reviews, documentation, and GitHub history** | **Groupwork** | **Both** |
| 5.12 | **Submit the final notebook PDF/HTML before the verified Canvas deadline; verify submission receipt/file** | **Final submission** | **jjustice; pwang verifies** |
| 5.13 | **Each member submits the Peer Evaluation Form separately** | **Individual submission** | **Each member** |
| 5.14 | **Check Canvas for Module 7 check-in and Discussion 7.1 requirements; complete if assigned** | **Separate course activity; verify** | **Each member** |
| 5.15 | **Check Canvas for the Final Assessment: Course Knowledge Quiz; complete if assigned** | **Separate course activity; verify** | **Each member** |

**[UPDATED] Target milestone: submit before the confirmed final deadline (original plan: Mon Oct 19, 11:59 PM PDT). The internal Oct 16 freeze provides time to fix export or reproducibility problems.**

### **[ADDED] Final Evidence Checklist**

**Add a requirement-to-notebook-section table to the final notebook using the actual section headings. Check these boxes only after reviewing the executed artifact.**

- [ ] **AF1: ticker-specific plan and corresponding execution are visible.**
- [ ] **AF2: actual tool choices, validated arguments, results, and responsive selection are visible.**
- [ ] **AF3: a draft and specific evidence-based self-critique are visible.**
- [ ] **AF4: a saved lesson, later retrieval, and its effect across runs are visible.**
- [ ] **WP1: all five stages, successive prompt inputs, and intermediate outputs are visible.**
- [ ] **WP2: routing to the implemented specialists and their outputs is visible.**
- [ ] **WP3: draft, feedback, changed draft, re-evaluation, and stopping status are visible.**
- [ ] **Integrated run: one ticker flows through planning, selected tools, routing, analysis, evaluation/refinement, and memory persistence.**
- [ ] **Code: readable executed PDF/HTML, explanatory Markdown/comments, workflow diagram and evaluation visualization, actual GitHub link, consistent repo/README, and PEP 8 review.**
- [ ] **Groupwork: both contributions documented, Module 4 update submitted, final notebook submitted, and individual peer evaluations completed.**

---

## Risks

| Risk | Mitigation |
| --- | --- |
| Local model too slow to iterate on | **Benchmark in 1.5; use a tested accessible fallback. Label cached model outputs when used, and preserve actual execution evidence for final demonstrations.** |
| Small model returns malformed JSON | **Validate/repair or retry within a cap; log failures and fallback use. Demonstrate genuine successful planning, selection, and evaluation.** |
| Notebook merge conflicts | Scratch notebooks plus the one-owner-at-a-time integration rule. |
| Optimizer loop never converges | **Three total drafts maximum; report unmet criteria and `needs_review` instead of calling the best score a successful pass.** |
| Uneven contribution affects individual grades | **Review substantive contributions weekly; use issues, reviews, code, and documentation alongside commit history. Rebalance work and contact the instructor promptly if collaboration problems block progress.** |
| PDF export mangles long outputs | **Condense repetitive logs only. Keep representative source text, final analyses, critiques, revisions, and memory evidence readable in full; use HTML if necessary. Inspect the first export by Oct 16.** |
| **News/API missing or limited** | **Verify returned fields early; label headline-only/summary-only input; use attributed frozen snapshots for reproducible replay and disclose the data date.** |
| **Unsupported statements survive evaluation** | **Use source-linked claim checks and a small manual review; disclose limitations rather than assuming the evaluator is infallible.** |
| **Scope expands beyond two-person capacity** | **Finish AF1–AF4 and WP1–WP3 first; defer optional RAG, additional models, and extra tickers.** |

---

## Cadence

Weekly engagement is required by the assignment.

- Zoom sync every Wednesday at 7:00 PM **(confirm the meeting timezone).**
- **Both members contribute meaningful work each week; track task, owner, status, review evidence, and next step in GitHub issues or a shared log.**
- **Integrate weekly from Week 2 onward; cross-review one another's demonstrations.**
- **Complete assigned module check-ins according to the verified Canvas instructions.**

### **[ADDED] Technical References for Implementation Checks**

**Use these primary documentation pages when checking the implementation; they do not add course requirements.**

- **[Hugging Face chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating): check the chat-template inputs and generation call against the installed version.**
- **[yfinance news API](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.get_news.html): inspect returned news records; do not assume full article bodies are supplied.**
- **[spaCy linguistic features](https://spacy.io/usage/linguistic-features): treat entity and part-of-speech annotations as model predictions requiring appropriate validation.**
