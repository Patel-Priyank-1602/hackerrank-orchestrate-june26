"""
Stage 5 — Risk Engine

Pure Python logic that combines image-based flags (from vision model)
with history-based flags (from user_history data) into a final
semicolon-separated risk_flags string.

Thresholds are calibrated against the sample_claims.csv expected outputs:
- user_history_risk: added when history_flags already contains it, OR rejected >= 3, 
  OR (rejected >= 1 AND last_90_days >= 3)
- manual_review_required: added when history_flags already contains it, OR last_90_days >= 5,
  OR (rejected >= 2 AND last_90_days >= 3)
"""

from config import ALLOWED_RISK_FLAGS


def compute_risk_flags(
    vision_flags: list,
    user_history: dict,
    suspicious_language: bool = False,
) -> str:
    """
    Combine image-based risk flags from the vision model with
    history-based risk flags computed from user_history.
    
    Returns a semicolon-separated string of risk flags, or "none".
    """
    flags = set()

    # ── Image-based flags (from vision model response) ────────────────────
    for flag in vision_flags:
        flag = str(flag).strip().lower()
        if flag and flag in ALLOWED_RISK_FLAGS and flag != "none":
            flags.add(flag)

    # ── Text-based flags ──────────────────────────────────────────────────
    if suspicious_language:
        flags.add("text_instruction_present")

    # ── History-based flags ───────────────────────────────────────────────
    if user_history:
        rejected = user_history.get("rejected_claim", 0)
        last_90 = user_history.get("last_90_days_claim_count", 0)
        manual_review = user_history.get("manual_review_claim", 0)
        history_flags_str = str(user_history.get("history_flags", "none"))

        # Parse existing history_flags from user_history.csv
        # These flags were pre-computed and should be included directly
        if history_flags_str and history_flags_str != "none":
            for hf in history_flags_str.split(";"):
                hf = hf.strip().lower()
                if hf and hf in ALLOWED_RISK_FLAGS and hf != "none":
                    flags.add(hf)

        # Additional threshold-based flags:
        # High rejected count → user_history_risk
        if rejected >= 3:
            flags.add("user_history_risk")

        # Moderate rejected + high recent frequency → user_history_risk  
        if rejected >= 1 and last_90 >= 3:
            flags.add("user_history_risk")

        # Very high recent claim frequency → manual_review_required
        if last_90 >= 5:
            flags.add("manual_review_required")

        # High rejected + moderate frequency → manual_review_required
        if rejected >= 2 and last_90 >= 3:
            flags.add("manual_review_required")

    # ── Final validation ──────────────────────────────────────────────────
    # Remove any flags not in allowed set
    flags = {f for f in flags if f in ALLOWED_RISK_FLAGS}

    if not flags:
        return "none"

    return ";".join(sorted(flags))
