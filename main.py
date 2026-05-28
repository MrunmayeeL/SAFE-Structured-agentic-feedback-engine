"""
SAFE: Structured Agentic Feedback Engine
Quick-start entry point.

Usage:
    python main.py                    # Run demo on first 5 QuixBugs programs
    python main.py --limit 25         # Run on 25 programs (full experiment)
    python main.py --task gcd         # Run on a specific task
"""

import sys
import os
import argparse

# Add src to path so modules resolve correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from loader import load_quixbugs
from safe.executor import run_test
from safe.classifier import classify_error
from safe.analyzer import extract_context
from safe.strategy import select_strategy
from safe.fixer import generate_fix_safe
from baseline.fixer import generate_fix_baseline
import difflib


def show_diff(old, new):
    print("\n===== CODE DIFF =====")
    for line in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm=""):
        print(line)


def run_safe(bug, max_iter=3):
    task_id = bug["task_id"]
    code = bug["code"]
    tests = bug["tests"]

    print(f"\n[SAFE] Repairing: {task_id}")
    for i in range(max_iter):
        result = run_test(code, tests)
        if result["success"]:
            print(f"  ✅ Fixed in {i+1} iteration(s)!")
            return True, i + 1

        error = result["error"]
        categories = classify_error(error)
        context = extract_context(error, code) or {"line": 0, "function_name": task_id, "snippet": code}
        strategies = select_strategy(categories)
        fixed = generate_fix_safe(categories, code, context.get("line"), error, strategies)
        if fixed:
            show_diff(code, fixed)
            code = fixed

    print("  ❌ Could not fix.")
    return False, max_iter


def run_baseline(bug, max_iter=3):
    task_id = bug["task_id"]
    code = bug["code"]
    tests = bug["tests"]

    print(f"\n[Baseline] Repairing: {task_id}")
    for i in range(max_iter):
        result = run_test(code, tests)
        if result["success"]:
            print(f"  ✅ Fixed in {i+1} iteration(s)!")
            return True, i + 1

        error = result["error"]
        fixed = generate_fix_baseline(code, error)
        if fixed:
            show_diff(code, fixed)
            code = fixed

    print("  ❌ Could not fix.")
    return False, max_iter


def main():
    parser = argparse.ArgumentParser(description="SAFE Quick Demo")
    parser.add_argument("--limit", type=int, default=5, help="Number of bugs to run (default: 5)")
    parser.add_argument("--task", type=str, default=None, help="Run a specific task by name")
    parser.add_argument("--dataset", type=str, default="benchmarks/QuixBugs", help="Path to QuixBugs")
    args = parser.parse_args()

    bugs = load_quixbugs(args.dataset)

    if args.task:
        bugs = [b for b in bugs if b["task_id"] == args.task]
        if not bugs:
            print(f"Task '{args.task}' not found.")
            return
    else:
        bugs = bugs[: args.limit]

    safe_results, baseline_results = [], []

    for bug in bugs:
        s, si = run_safe(bug)
        b, bi = run_baseline(bug)
        safe_results.append({"task_id": bug["task_id"], "success": s, "steps": si})
        baseline_results.append({"task_id": bug["task_id"], "success": b, "steps": bi})

    print("\n========== SUMMARY ==========")
    for label, results in [("SAFE", safe_results), ("Baseline", baseline_results)]:
        total = len(results)
        success = sum(1 for r in results if r["success"])
        print(f"{label}: {success}/{total} fixed ({success/total*100:.0f}%)")


if __name__ == "__main__":
    main()
