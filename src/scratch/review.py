"""Draft, self-evaluate and refine the research report (AF3, WP3)."""

import json
import re

import llm
import tools

ANALYST = (
    "You are an equity research analyst. Use only the supplied evidence. "
    "Quote numbers exactly as they appear in the evidence. Do not give "
    "buy/sell advice."
)
CRITIC = (
    "You are a fair, strict reviewer of equity research. Return one JSON "
    "object only."
)
CRITERIA = ("grounding", "coverage", "uncertainty", "clarity")
HEADINGS = ("Summary", "Market", "Earnings", "News", "Risks and Limitations")
PASS_MEAN = 4.0
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
RUBRIC = (
    "grounding: 5 = every number and claim appears in the evidence; "
    "3 = mostly supported, one or two vague or unsupported claims; "
    "1 = many invented facts.\n"
    "coverage: 5 = uses market, earnings and news evidence; 3 = one area "
    "thin; 1 = most evidence ignored.\n"
    "uncertainty: 5 = states the evidence limitations and missing data; "
    "3 = mentions risk generically; 1 = no limitations.\n"
    "clarity: 5 = concise, one idea per heading; 3 = repetitive or "
    "unfocused; 1 = hard to follow.\n"
    "Score what the note actually does. A good note should score 4 or 5."
)


def evidence_view(assembled):
    view = {}
    for name, sec in assembled["sections"].items():
        view[name] = {k: sec[k] for k in (
            "findings", "dates_units", "missing_data", "limitations")}
        if "metrics" in sec:
            view[name]["metrics"] = sec["metrics"]
        if "chain" in sec:
            view[name]["claims"] = [
                {"claim": c["claim"], "quote": c["quote"]}
                for c in sec["chain"]["claims"]]
    return json.dumps(view)


def _numbers(text):
    out = set()
    for n in NUM.findall(text):
        try:
            out.add(round(float(n.replace(",", "")), 2))
        except ValueError:
            pass
    return out


def unsupported_numbers(draft, evidence):
    known = _numbers(evidence)
    return sorted(
        n for n in _numbers(draft) - known
        if not (n.is_integer() and (n <= 12 or 1990 <= n <= 2100)))


def missing_headings(draft):
    return [h for h in HEADINGS if not re.search(
        rf"^\W*{h}\W*$", draft, re.MULTILINE | re.IGNORECASE)]


def draft_report(symbol, evidence, lessons=()):
    notes = "\n".join(f"- {n}" for n in lessons) or "- none"
    prompt = (
        f"Write a short research note on {symbol}. Put each of these "
        f"headings on its own line: {', '.join(HEADINGS)}. One or two "
        "sentences under each heading.\n"
        f"Lessons from earlier reviews:\n{notes}\n"
        f"EVIDENCE:\n{evidence}"
    )
    return llm.llm(prompt, max_new_tokens=700, temperature=0, system=ANALYST)


def evaluate_report(draft, evidence):
    prompt = (
        f"Score this research note from 1 to 5 on each criterion:\n{RUBRIC}\n"
        "List at most 4 specific issues, each under 20 words, and "
        "actionable feedback under 60 words. Only raise issues the writer "
        "can fix using the evidence; do not ask for data the evidence "
        "does not contain.\n"
        f"EVIDENCE:\n{evidence}\n\nNOTE:\n{draft}\n"
        '\nReturn {"scores": {"grounding": 4, "coverage": 4, '
        '"uncertainty": 3, "clarity": 5}, "issues": ["..."], '
        '"feedback": "..."} with your own scores.'
    )

    def check(obj):
        for c in CRITERIA:
            if obj["scores"][c] not in (1, 2, 3, 4, 5):
                raise ValueError(f"scores.{c} must be an integer 1-5")
        list(obj["issues"])

    obj = llm.llm_json(prompt, CRITIC, 600, validate=check)
    scores, issues = dict(obj["scores"]), list(obj["issues"])
    bad = unsupported_numbers(draft, evidence)
    if bad:
        scores["grounding"] = min(scores["grounding"], 2)
        issues.append(f"Numbers not found in the evidence: {bad}")
    gaps = missing_headings(draft)
    if gaps:
        scores["clarity"] = min(scores["clarity"], 2)
        issues.append(f"Missing headings: {gaps}")
    mean = sum(scores.values()) / len(scores)
    return {
        "scores": scores, "mean": round(mean, 2), "issues": issues,
        "feedback": obj["feedback"], "unsupported_numbers": bad,
        "missing_headings": gaps,
        "passed": mean >= PASS_MEAN and min(scores.values()) >= 3
        and not bad and not gaps,
    }


def refine_report(draft, evaluation, evidence, temperature=0):
    checks = [i for i in evaluation["issues"]
              if i.startswith(("Missing headings", "Numbers not found"))]
    issues = "\n".join(f"- {i}" for i in checks + [
        i for i in evaluation["issues"] if i not in checks])
    prompt = (
        f"EVIDENCE:\n{evidence}\n\nCURRENT NOTE:\n{draft}\n\n"
        f"A reviewer found these issues:\n{issues}\n"
        f"FEEDBACK: {evaluation['feedback']}\n\n"
        "Rewrite the note so every issue is fixed. Do not repeat the "
        "current note unchanged. Use exactly these headings, each on its "
        f"own line: {', '.join(HEADINGS)}. Only use numbers from the "
        "evidence."
    )
    return llm.llm(prompt, max_new_tokens=700, temperature=temperature,
                   system=ANALYST)


def make_lessons(symbol, history, plan, headlines):
    issues = [i for h in history for i in h["evaluation"]["issues"]]
    used = [f"{s['tool']}({s['args']})" for s in plan["steps"]]
    prompt = (
        f"A research run on {symbol} used these tool calls: {used}\n"
        "Its review raised these issues:\n"
        + "\n".join(f"- {i}" for i in issues)
        + f"\nAvailable tools: {list(tools.TOOLS)}\n"
        f"News headlines available to rag_query: {headlines}\n"
        f"Write 1 to 3 lessons for planning the next run on {symbol}. Each "
        "lesson must name one tool and say what to change: a different "
        "price period, or a rag_query question about a topic in the "
        "headlines above that the note missed. No financial figures.\n"
        'Answer like {"lessons": ["rag_query: ask about ... because ..."]}'
    )

    def check(obj):
        if not 1 <= len(obj["lessons"]) <= 3:
            raise ValueError("return 1 to 3 lessons")
        for lesson in obj["lessons"]:
            if not any(t in lesson for t in tools.TOOLS):
                raise ValueError(f"lesson must name a tool: {lesson!r}")

    try:
        return llm.llm_json(prompt, CRITIC, 200, validate=check)["lessons"]
    except ValueError:
        return []


def run_review_cycle(draft, evidence, symbol, plan, headlines=(),
                     max_drafts=3):
    history, stop_reason = [], f"reached {max_drafts}-draft limit"
    for n in range(1, max_drafts + 1):
        try:
            evaluation = evaluate_report(draft, evidence)
        except ValueError as e:
            stop_reason = f"evaluator failed: {e}"
            break
        history.append({"draft_number": n, "draft": draft,
                        "evaluation": evaluation})
        if evaluation["passed"]:
            stop_reason = "passed evaluation"
            break
        if n == max_drafts:
            break
        revised = refine_report(draft, evaluation, evidence)
        if revised.strip() == draft.strip():
            # Greedy decoding sometimes echoes the note verbatim.
            revised = refine_report(draft, evaluation, evidence, 0.7)
        if revised.strip() == draft.strip():
            stop_reason = "revision made no change"
            break
        draft = revised
    if not history:
        history.append({"draft_number": 1, "draft": draft,
                        "evaluation": {"mean": 0, "passed": False,
                                       "issues": [stop_reason]}})
    best = max(history, key=lambda h: h["evaluation"]["mean"])
    passed = history[-1]["evaluation"]["passed"]
    final = history[-1] if passed else best
    return {
        "final_report": final["draft"],
        "final_draft_number": final["draft_number"],
        "status": "passed" if passed else "needs_review",
        "stop_reason": stop_reason,
        "history": history,
        "lessons": make_lessons(symbol, history, plan, list(headlines)),
    }
