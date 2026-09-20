#!/usr/bin/env python
"""Score recorded trajectories against the rubric. Spends no API quota.

    python eval/score.py eval/results/baseline.jsonl
    python eval/score.py eval/results/baseline.jsonl eval/results/faulted.jsonl

Separated from run_eval.py on purpose: scoring can be re-run and audited
without touching the agent, and the raw trajectories stay the source of truth.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import unicodedata
from pathlib import Path

# Tools the agent may call that are not the answer-producing tool. "thinking"
# is reasoning scaffolding, so its presence never counts for or against
# tool selection.
SCAFFOLD_TOOLS = {"thinking"}


def normalise(text: str) -> str:
    """Rubric normalisation: presentation stripped, content preserved."""
    t = unicodedata.normalize("NFKC", text or "").lower()
    t = re.sub(r"[*_`]", "", t)                       # markdown emphasis
    t = "".join(" " if unicodedata.category(c) == "Zs" else c for c in t)
    t = re.sub(r"(?<=\d)[,\s]+(?=\d)", "", t)         # 832 040 / 832,040 -> 832040
    return re.sub(r"\s+", " ", t).strip()


# Found by reading all 30 baseline answers individually, after the automated
# question-leakage sweep passed them. In each of these the target string is
# satisfied by naming the source rather than answering the question, so a pass
# demonstrates nothing -- the same defect as code_07, but invisible to any
# check that only compares the target against the question text.
#
# All four questions were in fact answered correctly. They are excluded because
# the TEST cannot show it, not because the agent failed.
WEAK_TARGETS = {
    "code_07": "target '25' is one of the numbers listed in the question",
    "doc_04": "target 'image' appears in the paper's title, 'An Image is Worth 16x16 Words'",
    "doc_05": "target 'open neural network exchange' is just the ONNX acronym expansion",
    "doc_06": "target 'residual' appears in the paper's title, 'Deep Residual Learning'",
}


def target_is_weak(rec) -> bool:
    """True when a pass would not demonstrate the agent answered the question."""
    return rec["id"] in WEAK_TARGETS or target_leaks_into_question(rec)


def target_leaks_into_question(rec) -> bool:
    """True when the target string also appears in the question itself.

    Such a question is gradeable by echo: an answer that merely restates the
    input passes whether or not the agent computed anything, so the pass is
    not evidence. Detected automatically rather than by editing the frozen
    golden set, which rule 3 forbids once a run has happened.
    """
    spec = rec.get("answer_check")
    if not spec:
        return False
    q = normalise(rec.get("question", ""))
    targets = spec["target"] if spec["kind"] == "all_of" else [spec["target"]]
    return any(normalise(str(t)) in q for t in targets)


def check_answer(rec) -> bool | None:
    """True/False on the checkable subset, None when the question has no target."""
    spec = rec.get("answer_check")
    if not spec:
        return None
    hay = normalise(rec.get("final_answer", ""))
    targets = spec["target"] if spec["kind"] == "all_of" else [spec["target"]]
    return all(normalise(str(t)) in hay for t in targets)


def used_expected_tool(rec) -> bool:
    called = {t["tool"] for t in rec.get("tool_calls", []) if t["tool"] not in SCAFFOLD_TOOLS}
    return rec["expected_tool"] in called


def completed(rec) -> bool:
    """Rubric metric 4: produced a final answer with no error chunk."""
    return bool(rec.get("final_answer")) and not rec.get("error")


def score(path):
    recs = [json.loads(l) for l in open(path) if l.strip()]
    excluded = [r for r in recs if r.get("rate_limited")]
    kept = [r for r in recs if not r.get("rate_limited")]

    tool_hits = [used_expected_tool(r) for r in kept]
    checked = [(r, check_answer(r)) for r in kept]
    checkable = [(r, v) for r, v in checked if v is not None]
    unsound = [(r, v) for r, v in checkable if target_is_weak(r)]
    sound = [(r, v) for r, v in checkable if not target_is_weak(r)]
    lat = [r["latency_s"] for r in kept if completed(r)]

    out = {
        "file": str(path),
        "n_total": len(recs),
        "n_excluded_rate_limited": len(excluded),
        "n_scored": len(kept),
        "tool_selection_correct": sum(tool_hits),
        "tool_selection_pct": round(100 * sum(tool_hits) / len(kept), 1) if kept else 0,
        "task_success_correct": sum(1 for _, v in checkable if v),
        "task_success_n": len(checkable),
        "task_success_pct": round(100 * sum(1 for _, v in checkable if v) / len(checkable), 1)
                            if checkable else 0,
        # The number to quote: questions whose target cannot be satisfied by
        # echoing the prompt back.
        "task_success_sound_correct": sum(1 for _, v in sound if v),
        "task_success_sound_n": len(sound),
        "task_success_sound_pct": round(100 * sum(1 for _, v in sound if v) / len(sound), 1)
                                  if sound else 0,
        "unsound_targets": [r["id"] for r, _ in unsound],
        "completed": sum(completed(r) for r in kept),
        "completed_pct": round(100 * sum(completed(r) for r in kept) / len(kept), 1) if kept else 0,
        "median_latency_s": round(statistics.median(lat), 2) if lat else None,
        "p90_latency_s": round(sorted(lat)[max(0, int(0.9 * len(lat)) - 1)], 2) if lat else None,
        "errors": [{"id": r["id"], "error": (r["error"] or "")[:90]} for r in kept if r.get("error")],
    }

    by_cat = {}
    for r, v in checked:
        c = by_cat.setdefault(r["category"], {"n": 0, "tool_ok": 0, "chk": 0, "chk_ok": 0})
        c["n"] += 1
        c["tool_ok"] += used_expected_tool(r)
        if v is not None:
            c["chk"] += 1
            c["chk_ok"] += bool(v)
    out["by_category"] = by_cat
    out["failures"] = [
        {"id": r["id"], "expected": r["expected_tool"],
         "called": [t["tool"] for t in r["tool_calls"]],
         "answer_ok": v, "answer": (r.get("final_answer") or "")[:120]}
        for r, v in checked if not used_expected_tool(r) or v is False
    ]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    allout = []
    for f in args.files:
        s = score(f)
        allout.append(s)
        print(f"\n=== {Path(f).name}  ({s['n_scored']} scored"
              f"{', ' + str(s['n_excluded_rate_limited']) + ' excluded (rate limited)' if s['n_excluded_rate_limited'] else ''})")
        print(f"  tool selection : {s['tool_selection_correct']}/{s['n_scored']}  "
              f"({s['tool_selection_pct']}%)")
        print(f"  task success   : {s['task_success_sound_correct']}/{s['task_success_sound_n']}  "
              f"({s['task_success_sound_pct']}%)   [soundly gradeable subset -- QUOTE THIS]")
        if s["unsound_targets"]:
            print(f"                   (+{len(s['unsound_targets'])} excluded as weak targets, "
                  f"all answered correctly but not demonstrably so:")
            for wid in s["unsound_targets"]:
                print(f"                      {wid}: {WEAK_TARGETS.get(wid, 'echoes the question')}")
        print(f"  completed      : {s['completed']}/{s['n_scored']}  ({s['completed_pct']}%)")
        print(f"  latency        : median {s['median_latency_s']}s, p90 {s['p90_latency_s']}s")
        print("  by category    :")
        for c, v in sorted(s["by_category"].items()):
            print(f"      {c:<11s} tool {v['tool_ok']}/{v['n']}   answer {v['chk_ok']}/{v['chk']}")
        if s["failures"]:
            print("  failures:")
            for f_ in s["failures"]:
                print(f"      {f_['id']:<10s} expected {f_['expected']:<16s} "
                      f"called {f_['called']} answer_ok={f_['answer_ok']}")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(allout, indent=2))
        print(f"\n-> {args.json_out}")


if __name__ == "__main__":
    main()
