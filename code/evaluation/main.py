"""
Evaluation Module — Multi-Modal Evidence Review

Runs the pipeline on sample_claims.csv, compares output against expected values,
and generates evaluation_report.md with per-column accuracy metrics.

Also supports comparing two different prompt strategies.

Usage:
    python evaluation/main.py
"""

import sys
import os
import time
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Ensure code/ is on the Python path
CODE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE_DIR))

from config import (
    SAMPLE_CLAIMS_CSV, OUTPUT_CSV, OUTPUT_COLUMNS,
    GROQ_API_KEY,
)
from loader import load_claims


# ─── Columns to evaluate ─────────────────────────────────────────────────────
EVAL_COLUMNS = [
    "evidence_standard_met",
    "evidence_standard_met_reason",
    "risk_flags",
    "issue_type",
    "object_part",
    "claim_status",
    "claim_status_justification",
    "supporting_image_ids",
    "valid_image",
    "severity",
]

# Columns where exact match is expected
EXACT_MATCH_COLUMNS = [
    "evidence_standard_met",
    "issue_type",
    "object_part",
    "claim_status",
    "valid_image",
    "severity",
]

# Columns where we check set-overlap (semicolon-separated)
SET_MATCH_COLUMNS = [
    "risk_flags",
    "supporting_image_ids",
]

# Free-text columns (evaluated with keyword overlap)
TEXT_COLUMNS = [
    "evidence_standard_met_reason",
    "claim_status_justification",
]


def normalize(value: str) -> str:
    """Normalize a value for comparison."""
    return str(value).strip().lower()


def compare_exact(predicted: str, expected: str) -> bool:
    """Exact string match after normalization."""
    return normalize(predicted) == normalize(expected)


def compare_set(predicted: str, expected: str) -> float:
    """
    Compare semicolon-separated sets.
    Returns Jaccard similarity (intersection / union).
    """
    pred_set = set(s.strip().lower() for s in str(predicted).split(";") if s.strip())
    exp_set = set(s.strip().lower() for s in str(expected).split(";") if s.strip())

    if not pred_set and not exp_set:
        return 1.0
    if not pred_set or not exp_set:
        return 0.0

    intersection = pred_set & exp_set
    union = pred_set | exp_set
    return len(intersection) / len(union) if union else 0.0


def compare_text(predicted: str, expected: str) -> float:
    """
    Compare free-text fields using simple keyword overlap.
    Returns a score between 0.0 and 1.0.
    """
    pred_words = set(normalize(predicted).split())
    exp_words = set(normalize(expected).split())

    if not pred_words and not exp_words:
        return 1.0
    if not pred_words or not exp_words:
        return 0.0

    intersection = pred_words & exp_words
    # Use F1-like metric (harmonic mean of precision and recall)
    precision = len(intersection) / len(pred_words) if pred_words else 0
    recall = len(intersection) / len(exp_words) if exp_words else 0

    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def evaluate_predictions(predicted_df: pd.DataFrame, expected_df: pd.DataFrame) -> dict:
    """
    Compare predicted output against expected output row by row.
    Returns a dict with per-column metrics.
    """
    results = {col: {"correct": 0, "total": 0, "score_sum": 0.0, "details": []} for col in EVAL_COLUMNS}

    n = min(len(predicted_df), len(expected_df))

    for i in range(n):
        pred_row = predicted_df.iloc[i]
        exp_row = expected_df.iloc[i]

        for col in EVAL_COLUMNS:
            pred_val = str(pred_row.get(col, ""))
            exp_val = str(exp_row.get(col, ""))

            results[col]["total"] += 1

            if col in EXACT_MATCH_COLUMNS:
                match = compare_exact(pred_val, exp_val)
                results[col]["correct"] += int(match)
                results[col]["score_sum"] += 1.0 if match else 0.0
                results[col]["details"].append({
                    "row": i, "predicted": pred_val, "expected": exp_val, "match": match
                })

            elif col in SET_MATCH_COLUMNS:
                score = compare_set(pred_val, exp_val)
                results[col]["correct"] += int(score >= 0.5)
                results[col]["score_sum"] += score
                results[col]["details"].append({
                    "row": i, "predicted": pred_val, "expected": exp_val, "score": score
                })

            elif col in TEXT_COLUMNS:
                score = compare_text(pred_val, exp_val)
                results[col]["correct"] += int(score >= 0.3)
                results[col]["score_sum"] += score
                results[col]["details"].append({
                    "row": i, "predicted": pred_val[:80], "expected": exp_val[:80], "score": round(score, 2)
                })

    # Compute per-column accuracy/average score
    for col in EVAL_COLUMNS:
        total = results[col]["total"]
        if total > 0:
            if col in EXACT_MATCH_COLUMNS:
                results[col]["accuracy"] = results[col]["correct"] / total
            else:
                results[col]["avg_score"] = results[col]["score_sum"] / total

    return results


def generate_report(
    results: dict,
    strategy_name: str,
    num_claims: int,
    elapsed_seconds: float,
    num_images: int,
    report_path: str,
    append: bool = False,
) -> str:
    """Generate the evaluation_report.md content."""
    timestamp = datetime.now().isoformat()

    lines = []

    if not append:
        lines.append("# Evaluation Report — Multi-Modal Evidence Review\n")
        lines.append(f"Generated: {timestamp}\n")
        lines.append("---\n")

    lines.append(f"\n## Strategy: {strategy_name}\n")

    # Per-column accuracy table
    lines.append("### Per-Column Accuracy\n")
    lines.append("| Column | Type | Accuracy / Avg Score | Correct / Total |")
    lines.append("|--------|------|---------------------|-----------------|")

    overall_score = 0
    overall_count = 0

    for col in EVAL_COLUMNS:
        res = results[col]
        total = res["total"]
        if col in EXACT_MATCH_COLUMNS:
            acc = res.get("accuracy", 0)
            lines.append(f"| `{col}` | Exact Match | {acc:.1%} | {res['correct']}/{total} |")
            overall_score += acc
        elif col in SET_MATCH_COLUMNS:
            avg = res.get("avg_score", 0)
            lines.append(f"| `{col}` | Set Overlap | {avg:.1%} | {res['correct']}/{total} (≥50%) |")
            overall_score += avg
        elif col in TEXT_COLUMNS:
            avg = res.get("avg_score", 0)
            lines.append(f"| `{col}` | Text Overlap | {avg:.1%} | {res['correct']}/{total} (≥30%) |")
            overall_score += avg
        overall_count += 1

    if overall_count:
        lines.append(f"\n**Overall Average Score: {overall_score/overall_count:.1%}**\n")

    # Detailed mismatches for exact-match columns
    lines.append("\n### Detailed Mismatches (Exact Match Columns)\n")
    for col in EXACT_MATCH_COLUMNS:
        mismatches = [d for d in results[col]["details"] if not d.get("match", True)]
        if mismatches:
            lines.append(f"\n#### `{col}` — {len(mismatches)} mismatch(es)\n")
            lines.append("| Row | Predicted | Expected |")
            lines.append("|-----|-----------|----------|")
            for m in mismatches[:10]:  # limit to 10
                lines.append(f"| {m['row']} | `{m['predicted']}` | `{m['expected']}` |")

    # Operational analysis
    lines.append("\n---\n")
    lines.append("## Operational Analysis\n")
    lines.append(f"- **Claims processed**: {num_claims}")
    lines.append(f"- **Images processed**: {num_images}")
    lines.append(f"- **Total runtime**: {elapsed_seconds:.1f}s ({elapsed_seconds/max(num_claims,1):.1f}s per claim)")
    lines.append(f"- **Model calls per claim**: 2 (1× text parser + 1× vision analyzer)")
    lines.append(f"- **Total model calls**: {num_claims * 2}")
    lines.append(f"- **Approx input tokens**: ~{num_claims * 2000} (text) + ~{num_images * 1500} (images)")
    lines.append(f"- **Approx output tokens**: ~{num_claims * 400}")
    lines.append(f"- **Cost estimate (Groq free tier)**: $0.00 (free tier)")
    lines.append(f"- **TPM/RPM strategy**: {int(60 / max(2, 1))} RPM with {2}s sleep between claims")
    lines.append(f"- **Retry strategy**: Up to 3 retries with exponential backoff on 429 errors")
    lines.append(f"- **Caching**: No caching implemented (each claim is unique)")
    lines.append(f"- **Batching**: Single claim per API call (Groq does not support batch vision)")
    lines.append("")

    report_content = "\n".join(lines)

    mode = "a" if append else "w"
    with open(report_path, mode, encoding="utf-8") as f:
        f.write(report_content)

    return report_content


def run_evaluation():
    """
    Run the full evaluation:
    1. Process sample_claims.csv through the pipeline
    2. Compare against expected outputs
    3. Generate evaluation_report.md
    """
    print("=" * 60)
    print("  Evaluation — Multi-Modal Evidence Review")
    print("=" * 60)

    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set.")
        sys.exit(1)

    # Load expected data
    expected_df = load_claims(SAMPLE_CLAIMS_CSV)
    print(f"  Loaded {len(expected_df)} sample claims with expected outputs")

    # Count total images
    total_images = sum(
        len(str(row["image_paths"]).split(";"))
        for _, row in expected_df.iterrows()
    )

    # ── Strategy 1: Detailed Prompt (default) ─────────────────────────────
    print("\n--- Strategy 1: Detailed Prompt ---")
    from main import run_pipeline

    sample_output_path = str(CODE_DIR / "sample_output.csv")
    start = time.time()
    predicted_df = run_pipeline(
        input_csv=str(SAMPLE_CLAIMS_CSV),
        output_csv=sample_output_path,
    )
    elapsed1 = time.time() - start

    results1 = evaluate_predictions(predicted_df, expected_df)

    report_path = str(Path(__file__).resolve().parent / "evaluation_report.md")
    generate_report(
        results=results1,
        strategy_name="Detailed Prompt (comprehensive system prompt with full context)",
        num_claims=len(expected_df),
        elapsed_seconds=elapsed1,
        num_images=total_images,
        report_path=report_path,
        append=False,
    )

    print(f"\n✓ Evaluation report written to: {report_path}")

    # Print summary
    print("\n--- Quick Summary ---")
    for col in EXACT_MATCH_COLUMNS:
        acc = results1[col].get("accuracy", 0)
        print(f"  {col}: {acc:.1%}")


if __name__ == "__main__":
    run_evaluation()
