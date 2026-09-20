#!/usr/bin/env python
"""Run the golden set against the agent and append each trajectory to disk.

Grading lives in score.py, not here: this file only records what happened, so
a scoring change never requires re-spending API quota, and the raw
trajectories stay auditable.

    python eval/run_eval.py --out eval/results/baseline.jsonl
    python eval/run_eval.py --out eval/results/faulted.jsonl --fault-injection

Fault injection patches the PRIMARY provider's generate() to raise
RateLimitError on every call. The agent loop calls _call_llm_with_fallback at
every step, so the primary fails and the next provider takes over mid-run,
repeatedly -- that is the failover path the CV claim is about, not a provider
simply being absent at startup.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.chdir(ROOT / "backend")

from agent.graph import AgentRunner                      # noqa: E402
from agent.providers import RateLimitError               # noqa: E402

TIMEOUT_S = 180


def instrument_providers(runner, counter):
    """Count which provider actually served each LLM call.

    Free-tier primaries rate-limit constantly, so a run can be silently served
    by the fallbacks. Without this the fault-injection comparison is
    meaningless: you cannot tell a failover run from a baseline that was
    already failing over.
    """
    for provider, name in zip(runner.providers, runner.provider_names):
        original = provider.generate

        def wrapped(*a, _orig=original, _name=name, **kw):
            async def call():
                try:
                    r = await _orig(*a, **kw)
                    counter.setdefault(_name, {"ok": 0, "rate_limited": 0, "failed": 0})["ok"] += 1
                    return r
                except RateLimitError:
                    counter.setdefault(_name, {"ok": 0, "rate_limited": 0, "failed": 0})["rate_limited"] += 1
                    raise
                except Exception:
                    counter.setdefault(_name, {"ok": 0, "rate_limited": 0, "failed": 0})["failed"] += 1
                    raise
            return call()

        provider.generate = wrapped


def inject_primary_failure(runner):
    """Make the primary provider fail every call, forcing failover each step."""
    primary = runner.providers[0]
    name = runner.provider_names[0]

    async def always_rate_limited(*args, **kwargs):
        raise RateLimitError(f"injected fault: {name} disabled for this run",
                             retry_after=0.1)

    primary.generate = always_rate_limited
    return name


async def run_one(runner, item, counter):
    """Run one question. Returns a trajectory record; never raises."""
    t0 = time.perf_counter()
    counter.clear()
    rec = {
        "id": item["id"], "category": item["category"], "question": item["question"],
        "expected_tool": item["expected_tool"], "answer_check": item["answer_check"],
        "tool_calls": [], "final_answer": "", "error": None,
        "max_iterations_reached": False, "chunks": 0,
    }
    try:
        async def drive():
            async for chunk in runner.run(item["question"], mode="web"):
                rec["chunks"] += 1
                ctype = chunk.get("type")
                meta = chunk.get("metadata") or {}
                if ctype == "tool_call":
                    # graph.py puts the real name under metadata["tool"]; the
                    # content field is a display string ("Using web_search...").
                    rec["tool_calls"].append({"tool": meta.get("tool", ""),
                                              "input": meta.get("input")})
                elif ctype == "response":
                    rec["final_answer"] = chunk.get("content", "")
                    if meta.get("max_iterations_reached"):
                        rec["max_iterations_reached"] = True
                elif ctype == "error":
                    rec["error"] = chunk.get("content", "")[:400]

        await asyncio.wait_for(drive(), timeout=TIMEOUT_S)
    except asyncio.TimeoutError:
        rec["error"] = f"timeout after {TIMEOUT_S}s"
    except Exception as e:                      # noqa: BLE001 - record, never abort the run
        rec["error"] = f"{type(e).__name__}: {str(e)[:400]}"

    rec["latency_s"] = round(time.perf_counter() - t0, 2)
    rec["providers"] = {k: dict(v) for k, v in counter.items()}
    served = [k for k, v in counter.items() if v["ok"]]
    rec["served_by"] = served[0] if len(served) == 1 else served
    # Rubric rule 1: a rate-limited question is excluded from every metric.
    rec["rate_limited"] = bool(rec["error"] and "rate limit" in rec["error"].lower()
                               and "injected fault" not in rec["error"].lower())
    return rec


async def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--golden", default=str(ROOT / "eval" / "golden_set.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--fault-injection", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="pilot on the first N")
    ap.add_argument("--only", nargs="*", default=None, help="run specific ids")
    ap.add_argument("--pause", type=float, default=2.0, help="seconds between questions")
    args = ap.parse_args()

    gp = Path(args.golden)
    golden = json.loads((gp if gp.is_absolute() else ROOT / gp).read_text())
    if args.only:
        golden = [g for g in golden if g["id"] in set(args.only)]
    if args.limit:
        golden = golden[:args.limit]

    runner = AgentRunner()
    counter: dict = {}
    instrument_providers(runner, counter)
    mode = "baseline"
    if args.fault_injection:
        disabled = inject_primary_failure(runner)
        mode = f"fault_injection(primary={disabled} disabled)"
    print(f"providers: {runner.provider_names} | mode: {mode} | questions: {len(golden)}\n")

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out            # this module chdirs into backend/
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a") as f:                   # append: a crash cannot lose finished work
        for i, item in enumerate(golden, 1):
            rec = await run_one(runner, item, counter)
            rec["mode"] = mode
            f.write(json.dumps(rec) + "\n")
            f.flush()
            tools = ",".join(t["tool"] for t in rec["tool_calls"]) or "-"
            status = "ERR" if rec["error"] else "ok"
            print(f"[{i:2d}/{len(golden)}] {rec['id']:<10s} {status:<3s} "
                  f"{rec['latency_s']:6.1f}s  by:{str(rec['served_by'])[:16]:<16s} "
                  f"tools: {tools[:34]}")
            if rec["error"]:
                print(f"           -> {rec['error'][:110]}")
            await asyncio.sleep(args.pause)

    print(f"\nappended {len(golden)} trajectories -> {out}")


if __name__ == "__main__":
    asyncio.run(main())
