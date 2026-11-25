"""M4 evaluation: compare ReviewWise's complaint labels with hand-written gold labels.

Usage (from the repository root, with Ollama running):
    .venv/bin/python evaluation/run_eval.py --system keyword --label baseline-keyword
    .venv/bin/python evaluation/run_eval.py --system model --label m3-model
    .venv/bin/python evaluation/run_eval.py --system model --group-size 1 --label exp-group1

Each run writes evaluation/results/<label>.json (metrics) and <label>_cases.csv
(every case with gold and predicted labels) and prints a Markdown results row.
"""

import argparse
import csv
import json
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from reviewwise.config import CATEGORIES  # noqa: E402

CASES = ROOT / "evaluation/cases.csv"
RESULTS = ROOT / "evaluation/results"

# Naive baseline: lowercase keyword prefixes per category, no AI. Deliberately simple.
KEYWORDS = {
    "slow_service": ["slow", "wait", "lent", "attendu", "attente", "langsam", "warten", "gewartet", "lues", "gewaart"],
    "cold_coffee": ["cold", "lukewarm", "froid", "tiède", "kalt", "lauwarm", "kal"],
    "high_prices": ["expensive", "price", "pricey", "cher", "prix", "teuer", "preis", "deier", "präisser"],
    "dirty_tables": ["dirty", "clean", "sticky", "sale", "propre", "schmutzig", "sauber", "dreckeg"],
    "incorrect_order": ["wrong", "instead", "falsch", "au lieu", "erreur"],
    "unfriendly_staff": ["rude", "unfriendly", "impoli", "désagréable", "unfreundlich", "net frëndlech"],
}


def load_cases(path=CASES, subset=None):
    with open(path, encoding="utf-8") as handle:
        cases = list(csv.DictReader(handle))
    for case in cases:
        case["gold"] = set(filter(None, case["gold_complaints"].split(";")))
        unknown = case["gold"] - set(CATEGORIES)
        if unknown:
            raise ValueError(f"{case['case_id']}: unknown gold category {unknown}")
    return [case for case in cases if subset in (None, "all", case["set"])]


def keyword_labels(text):
    lowered = text.lower()
    return {
        category for category, words in KEYWORDS.items()
        if any(re.search(r"(?<!\w)" + re.escape(word), lowered) for word in words)
    }


def run_keyword(cases):
    start = time.perf_counter()
    predictions = [keyword_labels(case["review"]) for case in cases]
    return predictions, {"total_seconds": time.perf_counter() - start, "request_seconds": [], "failures": 0, "ai_requests": 0}


def run_model(cases, group_size=None, warmup=True):
    from reviewwise import pipeline
    from reviewwise.pipeline import Review, analyze_reviews

    if group_size:
        # Experiment only: replace the app's grouping (<=4 reviews, <=1500 bytes) with fixed-size groups.
        pipeline.review_groups = lambda reviews: (reviews[i:i + group_size] for i in range(0, len(reviews), group_size))

    timings = []
    original = pipeline.extract_group

    def timed(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            timings.append(time.perf_counter() - started)

    pipeline.extract_group = timed
    if warmup:  # load the model into memory so latency measures analysis, not model loading
        analyze_reviews([Review(1, "Warm-up review.")])
        timings.clear()
    reviews = [Review(number, case["review"]) for number, case in enumerate(cases, 1)]
    start = time.perf_counter()
    result = analyze_reviews(reviews)
    total = time.perf_counter() - start
    pipeline.extract_group = original
    if result.stop_reason:
        print(f"WARNING: analysis stopped early: {result.stop_reason}", file=sys.stderr)
    by_number = {a.review.number: {c.category for c in a.extraction.complaints} for a in result.analyses}
    failed = {f.review.number for f in result.failures} | {r.number for r in result.pending}
    # A review the app could not analyse counts as "no complaints found" (that is what the user sees).
    predictions = [by_number.get(number, set()) for number in range(1, len(cases) + 1)]
    for number in failed:
        cases[number - 1]["failed"] = True
    return predictions, {
        "total_seconds": total, "request_seconds": timings, "failures": len(failed),
        "ai_requests": result.ai_requests, "model": result.model_name, "model_digest": result.model_digest,
    }


def score(cases, predictions):
    tp = fp = fn = exact = detect = 0
    gold_counts = {c: 0 for c in CATEGORIES}
    pred_counts = {c: 0 for c in CATEGORIES}
    for case, predicted in zip(cases, predictions):
        gold = case["gold"]
        tp += len(gold & predicted)
        fp += len(predicted - gold)
        fn += len(gold - predicted)
        exact += gold == predicted
        detect += bool(gold) == bool(predicted)
        for c in gold:
            gold_counts[c] += 1
        for c in predicted:
            pred_counts[c] += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    def top(counts):
        best = max(counts.values())
        return sorted(c for c, n in counts.items() if n == best and n > 0)

    return {
        "cases": len(cases),
        "exact_match": exact / len(cases),
        "complaint_detection_accuracy": detect / len(cases),
        "precision": precision, "recall": recall, "f1": f1,
        "tp": tp, "fp": fp, "fn": fn,
        "count_abs_error": sum(abs(gold_counts[c] - pred_counts[c]) for c in CATEGORIES),
        "gold_counts": gold_counts, "predicted_counts": pred_counts,
        "top_issue_gold": top(gold_counts), "top_issue_predicted": top(pred_counts),
    }


def latency(info, n_cases):
    times = info["request_seconds"]
    return {
        "total_seconds": round(info["total_seconds"], 2),
        "seconds_per_review": round(info["total_seconds"] / n_cases, 3),
        "request_median_seconds": round(statistics.median(times), 2) if times else None,
        "request_max_seconds": round(max(times), 2) if times else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--system", choices=["model", "keyword"], required=True)
    parser.add_argument("--label", required=True, help="Name for the result files, e.g. m3-model.")
    parser.add_argument("--set", default="all", choices=["all", "workbook", "hard"])
    parser.add_argument("--group-size", type=int, help="Experiment: fixed number of reviews per AI request.")
    parser.add_argument("--no-warmup", action="store_true")
    args = parser.parse_args()

    cases = load_cases(subset=args.set)
    if args.system == "keyword":
        predictions, info = run_keyword(cases)
    else:
        predictions, info = run_model(cases, args.group_size, warmup=not args.no_warmup)

    sets = sorted({case["set"] for case in cases})
    metrics = {"overall": score(cases, predictions)}
    for name in sets:
        chosen = [(c, p) for c, p in zip(cases, predictions) if c["set"] == name]
        metrics[name] = score([c for c, _ in chosen], [p for _, p in chosen])

    RESULTS.mkdir(parents=True, exist_ok=True)
    document = {
        "label": args.label, "system": args.system, "group_size": args.group_size or "app default",
        "run_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "latency": latency(info, len(cases)),
        "failures": info["failures"], "ai_requests": info["ai_requests"],
        "model": info.get("model"), "model_digest": info.get("model_digest"),
        "metrics": metrics,
    }
    (RESULTS / f"{args.label}.json").write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with open(RESULTS / f"{args.label}_cases.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["case_id", "set", "language", "review", "gold", "predicted", "correct", "failed"])
        for case, predicted in zip(cases, predictions):
            writer.writerow([
                case["case_id"], case["set"], case["language"], case["review"],
                ";".join(sorted(case["gold"])), ";".join(sorted(predicted)),
                "yes" if case["gold"] == predicted else "NO", "yes" if case.get("failed") else "",
            ])

    print("| Run | Set | Exact match | Precision | Recall | F1 | Count error | Top issue | s/review |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, m in metrics.items():
        top_ok = "correct" if m["top_issue_predicted"] == m["top_issue_gold"] else "wrong: " + ", ".join(m["top_issue_predicted"])
        print(f"| {args.label} | {name} ({m['cases']}) | {m['exact_match']:.0%} | {m['precision']:.0%} | "
              f"{m['recall']:.0%} | {m['f1']:.2f} | {m['count_abs_error']} | {top_ok} | {document['latency']['seconds_per_review']} |")
    print(f"\nFailures: {info['failures']} · AI requests: {info['ai_requests']} · latency: {document['latency']}")
    print(f"Saved evaluation/results/{args.label}.json and {args.label}_cases.csv")


if __name__ == "__main__":
    main()
