"""Acceptance scenarios for every requirement, end to end.

AAPL twice from a fresh memory file (AF4), then TSLA, which has no local cache
(AF2: live tools, different tool choices).

    uv run python src/scratch/demo.py
"""

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

import review  # noqa: E402
import tools  # noqa: E402
from agent import ResearchAgent  # noqa: E402

PLOT_DIR = tools.DATA_DIR.parent / "evidence"


def calls(trace):
    return [f"{s['tool']}({', '.join(f'{k}={v}' for k, v in s['args'].items()
                                     if k != 'symbol')})"
            for s in trace["plan"]["steps"]]


def show(title, rows):
    print(f"\n=== {title}")
    for row in rows:
        print(f"  {row}")


def seeded_refinement(trace):
    draft = trace["review"]["history"][0]["draft"]
    weak = draft.split("Risks")[0] + "\nAnalysts expect 87.3% upside."
    return review.run_review_cycle(weak, trace["evidence"], trace["symbol"],
                                   trace["plan"])


def plot_scores(runs, path):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    for label, trace in runs:
        means = [h["evaluation"]["mean"] for h in trace["review"]["history"]]
        ax.plot(range(1, len(means) + 1), means, marker="o", label=label)
    ax.axhline(4.0, ls="--", color="grey", lw=1, label="pass threshold")
    ax.set(xlabel="draft", ylabel="mean evaluator score", ylim=(1, 5),
           title="Evaluator-optimizer iterations")
    ax.xaxis.get_major_locator().set_params(integer=True)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)


def plot_prices(symbol, path):
    close = tools.get_prices(symbol, "1y")["Close"]
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(close.index, close, label="close")
    for n in (50, 200):
        ax.plot(close.index, close.rolling(n).mean(), label=f"{n}-day MA")
    ax.set(title=f"{symbol} price", ylabel="USD")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)


def main():
    agent = ResearchAgent(Path(tempfile.mkdtemp()) / "memory.json")
    aapl1 = agent.process("AAPL")
    aapl2 = agent.process("AAPL")
    tsla = agent.process("TSLA")
    seeded = {"review": seeded_refinement(aapl1)}
    runs = [("AAPL run 1", aapl1), ("AAPL run 2", aapl2), ("TSLA", tsla),
            ("seeded weak draft", seeded)]

    agents = runs[:3]
    show("AF1/AF2 plans (source, tool calls)",
         [f"{label}: {t['plan']['source']} {calls(t)}" for label, t in agents])
    show("AF2 tool errors", [
        f"{label}: {s['tool']} {s['error']}" for label, t in agents
        for s in t["tool_calls"] if s["error"]] or ["none"])
    show("WP2 routes", [
        f"{label}: {r['tool']} -> {r['route']} ({r['source']})"
        for label, t in agents for r in t["routes"]])
    show("WP3 review", [
        f"{label}: {t['review']['status']} ({t['review']['stop_reason']}), "
        f"means {[h['evaluation']['mean'] for h in t['review']['history']]}"
        for label, t in runs])
    show("WP3 seeded weak draft: issues per draft (labeled example)", [
        f"draft {h['draft_number']}: {h['evaluation']['issues']}"
        for h in seeded["review"]["history"]])
    show("AF4 memory", [
        f"run 1 saved: {aapl1['lessons_saved']}",
        f"run 2 loaded: {aapl2['lessons_loaded']}",
        f"plan changed: {calls(aapl1) != calls(aapl2)}",
    ])
    show("Final AAPL report (run 2)", [aapl2["review"]["final_report"]])

    PLOT_DIR.mkdir(exist_ok=True)
    plot_scores(runs, PLOT_DIR / "review_scores.png")
    plot_prices("AAPL", PLOT_DIR / "AAPL_price.png")
    print(f"\nPlots in {PLOT_DIR}")


if __name__ == "__main__":
    main()
