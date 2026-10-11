# Financial agent review progress — October 11, 2026

This contribution adds independent human review, complete run snapshots, approved-only Memory, and diagnosable Critic feedback to Jason's reference notebook. The saved runs demonstrate traceability, error detection, and conservative stopping. They do not demonstrate improved financial accuracy or a completed Writer correction cycle.

## Files in this submission

| File | Purpose |
| --- | --- |
| `src/scratch/investment_research_agent_review.ipynb` | English source notebook; outputs cleared; model, research, and replay disabled by default. |
| `data/demo/review_20261011/investment_research_agent_review_executed.ipynb` | English explanations with the uploaded run outputs and execution settings preserved. Historical evidence, not the default run entry point. |
| `data/demo/review_20261011/offline_validation.json` | Locally rerun synthetic test results: 21 review checks plus 21 Critic checks; 30 code cells executed; zero live model calls. |
| `data/demo/review_20261011/submission_manifest.json` | Source/deliverable hashes and exact external run files still needed for replay. |
| This README | Results, limitations, reproduction instructions, and proposed next work. |

Full run bundles and reviewed labels are not embedded in these files. Add the existing Colab exports listed below; do not reconstruct snapshots from displayed tables. The delivery preparation did not have those original external files and did not fabricate them.

## Implemented changes

- **Human review:** export retrieval, claim extraction, summary, and final-report rows with their supporting text; import labels against the matching baseline. Only `human_verdict`, `human_reviewer`, and `human_note` are editable. Changed source text and missing rows are rejected.
- **Separate statuses:** automatic passing and human review completion are distinct. Completing all labels can still leave unsupported or insufficiently supported content.
- **Frozen replay:** preserve evidence, first draft, evaluation history, source trace, and runtime settings. Check input integrity and compare the same evidence/draft without running Planner or live tools again.
- **Memory approval:** new lessons start pending. Only explicitly approved lessons with evidence and tool-capability checks reach Planner. A report review does not approve Memory.
- **Critic diagnostics:** split scores from one ID-based proposal, validate schemas and IDs, retry invalid IDs, record raw responses and actual token budgets. Invalid/unresolved feedback blocks Writer and automatic passing.
- **Offline execution:** optional model/research switches support CPU-only review and synthetic validation.

Planner, Router, news-chain processing, and specialist code are unchanged from the supplied Jason reference. Numeric-presence, required-heading, and duplicate-line checks existed in that reference; they are not new additions. The stricter Critic changes both prompts and stopping behavior.

## Latest saved results

| Example | Approved lessons loaded | Evaluated drafts | Mean scores | Result / Writer |
| --- | ---: | ---: | --- | --- |
| AAPL Run 1 | 0 | 1 | 5.00 | `needs_review`; semantic concern pending; no Writer revision |
| AAPL Run 2 | 0 | 1 | 5.00 | `needs_review`; semantic concern pending; no Writer revision |
| TSLA original | 0 | 0 | No score | `needs_review`; scoring JSON rejected twice |
| Seeded AAPL weak draft | Reuses AAPL evidence | 1 | 3.50 | Defects detected; human gate stops Writer; defects remain |
| TSLA frozen replay | Planner not run | 1 | 3.50 | Scoring succeeded; proposal failed; Writer disabled |

The newly exported AAPL Run 1, Run 2, and TSLA audits contain 14, 14, and 17 pending rows. Added cell E was skipped in this execution. Peng previously reported completing a separate 14-row audit; that historical completion does not apply to these new rows. Keep any completed CSV with its exact matching baseline and import result.

The original overlapping score plot excludes the later frozen TSLA result. Empty TSLA history means no completed evaluation, not a zero score. The threshold line alone does not establish passing.

## What the TSLA replay establishes

Original scoring outputs included `coverage: 7`, omitted `clarity`, and added unrecognized fields. After appending explicit output requirements to the scoring prompt, the saved replay produced valid raw scores `5/5/2/5`. The existing heading check capped clarity at 2 because the report used `Limitations:` instead of `Risks and Limitations:`, resulting in mean 3.50. Limitation text was present; this was an exact-heading failure.

The proposal's first attempt reached its 180-token output limit; the retry completed but used the unsupported kind `disclaim`. The report remained unchanged. This is one observed scoring-format recovery, not evidence of reliable proposal generation or factual improvement.

- Snapshot: `tsla_20261011T165624476503Z.json`
- Frozen experiment: `tsla_20261011T172130147986Z.json`
- Evidence SHA-256: `d1bf1b39be433f5f2cbc26b548f4d7c21b33080d1e2e9a389a76042552ebcb57`
- Initial-draft SHA-256: `7291e21d7110561bd7ac0209a0109923d31f5ebad0719e4ac23c24c62f61fe2c`

## Limits on comparison with Jason's original notebook

The supplied `investment_research_agent_v0_Jason.ipynb` has these saved results: AAPL Run 1 4.25/pass, AAPL Run 2 4.75/pass, TSLA 3.25 → 2.75 → 3.25/needs_review, and weak draft 2.75 → 4.75/pass. Those runs are not a matched-input comparison with the October 11 full runs. Input data, Memory, evaluator instructions, and stopping rules can differ. The newer scores and fewer automatic passes cannot establish either improved accuracy or worse reports.

## Known limitations and reviewer comments

1. **Feedback usability remains experimental.** Correct R/E IDs locate text but do not prove a claim is supported or wrong. Pending semantic concerns currently stop revisions. CSV import has no resume-Writer pathway.
2. **AAPL intermediate grounding:** the saved summary infers an earnings impact from the Qualcomm cash-source/departure text. The displayed claim does not establish that impact.
3. **TSLA intermediate/output issues:** news summarization failed; fallback findings reached the report. Some extraction wording infers a change in capabilities/regulatory status from a product rename. Gross-profit growth, margins, and dollar values need clearer concepts; net-income changes need explicit QoQ/YoY labels.
4. **Memory benefit not demonstrated:** no approved lesson was loaded in either new AAPL run. A pending lesson links a JEPQ retirement-budget headline to Apple's financial health, illustrating the need for review before reuse.
5. **Prompt provenance is incomplete:** `CRITIC_VERSION` still says `v3.1-id-validation-retry`. The constant-based prompt hash omits the inline scoring suffix. Retain the notebook and full frozen `llm_calls`; do not treat that hash as a fingerprint of every prompt change.
6. **Latest source and historical outputs differ in timing:** the score prompt suffix was added after the initial TSLA failure. The later proposed proposal suffix and a separate Writer-only test are not implemented in the uploaded source.
7. **Tests are synthetic:** passing 42 checks verifies the tested software behavior, not financial facts. This English delivery performed no live inference.

## Exact Colab artifacts to add

All paths below were printed by the saved notebook under `/content/data/`.

| Experiment | Download ZIP | Snapshot inside the run export |
| --- | --- | --- |
| AAPL Run 1 | `aapl_review_20261011T164604153696Z.zip` | `aapl_20261011T164604145146Z.json` |
| AAPL Run 2 | `aapl_review_20261011T165140947257Z.zip` | `aapl_20261011T165140938488Z.json` |
| TSLA original | `tsla_review_20261011T165624485162Z.zip` | `tsla_20261011T165624476503Z.json` |
| Weak draft | `aapl_review_20261011T165849637550Z.zip` | `aapl_20261011T165849629105Z.json` |
| TSLA frozen replay | `frozen_review_20261011T172130156960Z.zip` | Original TSLA snapshot plus new experiment JSON |

Preserve each CSV and its own baseline JSON. Place extracted files in separate subfolders under `runs/aapl_run_1`, `runs/aapl_run_2`, `runs/tsla_original`, `runs/weak_draft`, and `runs/tsla_frozen`. Keep the latest `memory_review.json` under `state/`. Keep older Memory copies inside their run bundle folders; do not mistake them for the latest state.

If full AAPL research reproduction is needed, include the exact `AAPL_prices.csv`, `AAPL_financials.csv`, and `AAPL_news.json` used under `inputs/`. Frozen Critic replay only needs the snapshot and model environment. Do not fetch replacement live inputs and label them as the original run data.

## Run and review

1. Open the clean notebook, leave its defaults off, and run all on CPU. H and H.1 should each report 21 passing checks.
2. To review evidence, use a saved CSV/baseline pair and import completed labels in E. Review Memory separately in F. No GPU is needed for those operations.
3. For frozen inference, load the model, run definitions through C, and set the snapshot path in G. Keep Writer disabled with one draft slot for Critic-only testing. Compare exact feedback/errors on identical evidence and first-draft hashes.
4. A later Writer experiment should measure defect removal, preservation of supported content, and remaining human concerns. Two draft slots permit a revision but do not force it. Do not mark an unresolved run passed to obtain a curve.
5. Submit this as one experimental draft PR on the agreed weekly branch. Keep Jason's production workflow separate until the team agrees which changes to integrate.


