"""
Multi-Modal Evidence Review — Main Pipeline

Orchestrates all 6 stages:
  1. Load All Inputs
  2. Claim Text Parsing (llama-3.3-70b-versatile on Groq)
  3. Encode Images as Base64
  4. Vision Analysis (llama-4-scout-17b-16e-instruct on Groq)
  5. Risk Engine (pure Python)
  6. Output Builder (pandas)

Usage:
    python main.py                          # Process claims.csv → output.csv
    python main.py --sample                 # Process sample_claims.csv → sample_output.csv
    python main.py --input path/to/file.csv --output path/to/out.csv
"""

import sys
import os
import time
import argparse
import pandas as pd
from pathlib import Path

# Ensure code/ is on the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    CLAIMS_CSV, SAMPLE_CLAIMS_CSV,
    OUTPUT_CSV, OUTPUT_COLUMNS,
    SLEEP_BETWEEN_CLAIMS, GROQ_API_KEY,
)
from loader import (
    load_claims, load_user_history,
    load_evidence_requirements, get_relevant_requirements,
)
from text_parser import parse_claim_text
from image_encoder import prepare_image_blocks
from vision_analyzer import analyze_images_with_vision, build_claim_context
from risk_engine import compute_risk_flags
from output_builder import build_output_row


def process_single_claim(
    row: pd.Series,
    user_history: dict,
    evidence_requirements: dict,
    claim_index: int,
    total_claims: int,
) -> dict:
    """Process a single claim through all stages and return the output row dict."""
    user_id = str(row["user_id"])
    image_paths = str(row["image_paths"])
    user_claim = str(row["user_claim"])
    claim_object = str(row["claim_object"]).strip().lower()

    print(f"\n{'='*60}")
    print(f"  Claim {claim_index + 1}/{total_claims} | User: {user_id} | Object: {claim_object}")
    print(f"  Images: {image_paths}")
    print(f"{'='*60}")

    # ── Stage 2: Claim Text Parsing ───────────────────────────────────────
    print("  [Stage 2] Parsing claim text...")
    parsed_claim = parse_claim_text(user_claim, claim_object)
    print(f"    → Damage: {parsed_claim.get('claimed_damage_types', [])}")
    print(f"    → Parts: {parsed_claim.get('claimed_object_parts', [])}")
    print(f"    → Suspicious: {parsed_claim.get('suspicious_language', False)}")

    # ── Stage 3: Encode Images ────────────────────────────────────────────
    print("  [Stage 3] Encoding images...")
    image_blocks, image_ids = prepare_image_blocks(image_paths)
    print(f"    → {len(image_blocks)} images encoded: {image_ids}")

    if not image_blocks:
        print("    ⚠ No valid images found!")
        # Return a minimal row with no-image results
        return build_output_row(
            user_id=user_id,
            image_paths=image_paths,
            user_claim=user_claim,
            claim_object=claim_object,
            vision_result={
                "valid_image": False,
                "evidence_standard_met": False,
                "evidence_standard_met_reason": "No valid images could be loaded.",
                "issue_type": "unknown",
                "object_part": "unknown",
                "severity": "unknown",
                "claim_status": "not_enough_information",
                "claim_status_justification": "No images available for review.",
                "supporting_image_ids": ["none"],
                "risk_flags_from_images": [],
            },
            risk_flags=compute_risk_flags(
                [], user_history.get(user_id, {}), False
            ),
            available_image_ids=image_ids,
            parsed_claim=parsed_claim,
        )

    # ── Get relevant evidence requirements ────────────────────────────────
    evidence_rules = get_relevant_requirements(claim_object, evidence_requirements)

    # ── Stage 4: Vision Analysis ──────────────────────────────────────────
    print("  [Stage 4] Running vision analysis...")
    hist = user_history.get(user_id, {})
    claim_context = build_claim_context(
        claim_object=claim_object,
        user_claim=user_claim,
        parsed_claim=parsed_claim,
        user_history=hist,
        evidence_rules=evidence_rules,
        image_ids=image_ids,
    )
    vision_result = analyze_images_with_vision(image_blocks, image_ids, claim_context)
    print(f"    → Status: {vision_result.get('claim_status')}")
    print(f"    → Issue: {vision_result.get('issue_type')}")
    print(f"    → Part: {vision_result.get('object_part')}")
    print(f"    → Valid image: {vision_result.get('valid_image')}")
    print(f"    → Severity: {vision_result.get('severity')}")

    # ── Stage 5: Risk Engine ──────────────────────────────────────────────
    print("  [Stage 5] Computing risk flags...")
    vision_flags = vision_result.get("risk_flags_from_images", [])
    suspicious = parsed_claim.get("suspicious_language", False)
    risk_flags = compute_risk_flags(vision_flags, hist, suspicious)
    print(f"    → Flags: {risk_flags}")

    # ── Stage 6: Build Output Row ─────────────────────────────────────────
    print("  [Stage 6] Building output row...")
    output_row = build_output_row(
        user_id=user_id,
        image_paths=image_paths,
        user_claim=user_claim,
        claim_object=claim_object,
        vision_result=vision_result,
        risk_flags=risk_flags,
        available_image_ids=image_ids,
        parsed_claim=parsed_claim,
    )
    print(f"    ✓ Row complete")

    return output_row


def run_pipeline(input_csv: str = None, output_csv: str = None):
    """
    Main pipeline entry point.
    Processes all claims and writes output CSV.
    """
    # Validate API key
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY environment variable is not set.")
        print("Set it with: export GROQ_API_KEY=your_key_here")
        print("Or create a .env file in the code/ directory with: GROQ_API_KEY=your_key_here")
        sys.exit(1)

    input_path = input_csv or str(CLAIMS_CSV)
    output_path = output_csv or str(OUTPUT_CSV)

    print("=" * 60)
    print("  Multi-Modal Evidence Review Pipeline")
    print("=" * 60)
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_path}")
    print()

    # ── Stage 1: Load All Inputs ──────────────────────────────────────────
    print("[Stage 1] Loading inputs...")
    claims_df = load_claims(input_path)
    user_history = load_user_history()
    evidence_requirements = load_evidence_requirements()
    print(f"  → {len(claims_df)} claims loaded")
    print(f"  → {len(user_history)} user history records")
    print(f"  → {len(evidence_requirements)} evidence requirements")

    # ── Process each claim ────────────────────────────────────────────────
    output_rows = []
    total = len(claims_df)
    start_time = time.time()

    for idx, row in claims_df.iterrows():
        try:
            output_row = process_single_claim(
                row, user_history, evidence_requirements, len(output_rows), total
            )
            output_rows.append(output_row)
        except Exception as e:
            print(f"  ✗ ERROR processing claim {idx}: {e}")
            import traceback
            traceback.print_exc()
            # Create a fallback row
            output_rows.append({
                "user_id": str(row["user_id"]),
                "image_paths": str(row["image_paths"]),
                "user_claim": str(row["user_claim"]),
                "claim_object": str(row["claim_object"]),
                "evidence_standard_met": "false",
                "evidence_standard_met_reason": f"Processing error: {str(e)[:100]}",
                "risk_flags": "none",
                "issue_type": "unknown",
                "object_part": "unknown",
                "claim_status": "not_enough_information",
                "claim_status_justification": "Error during processing.",
                "supporting_image_ids": "none",
                "valid_image": "false",
                "severity": "unknown",
            })

        # Rate limiting: sleep between claims to avoid Groq limits
        if len(output_rows) < total:
            print(f"  ⏳ Waiting {SLEEP_BETWEEN_CLAIMS}s (rate limiting)...")
            time.sleep(SLEEP_BETWEEN_CLAIMS)

    # ── Write Output ──────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"  Pipeline complete!")
    print(f"  Processed: {len(output_rows)}/{total} claims")
    print(f"  Time: {elapsed:.1f}s ({elapsed/total:.1f}s per claim)")
    print(f"{'='*60}")

    output_df = pd.DataFrame(output_rows, columns=OUTPUT_COLUMNS)
    output_df.to_csv(output_path, index=False, quoting=1)  # quoting=1 = QUOTE_ALL
    print(f"\n✓ Output written to: {output_path}")

    return output_df


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Modal Evidence Review Pipeline"
    )
    parser.add_argument(
        "--sample", action="store_true",
        help="Process sample_claims.csv instead of claims.csv"
    )
    parser.add_argument(
        "--input", type=str, default=None,
        help="Custom input CSV path"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Custom output CSV path"
    )

    args = parser.parse_args()

    if args.sample:
        input_csv = str(SAMPLE_CLAIMS_CSV)
        output_csv = args.output or str(
            Path(OUTPUT_CSV).parent / "sample_output.csv"
        )
    else:
        input_csv = args.input or str(CLAIMS_CSV)
        output_csv = args.output or str(OUTPUT_CSV)

    run_pipeline(input_csv, output_csv)


if __name__ == "__main__":
    main()
