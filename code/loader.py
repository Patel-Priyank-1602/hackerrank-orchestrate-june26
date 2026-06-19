"""
Stage 1 — Load All Inputs

Loads claims CSV, user history (dict by user_id), and evidence requirements
(dict by (claim_object, applies_to)). Images are not loaded here; only paths
are noted from the CSV.
"""

import pandas as pd
from typing import Dict, Tuple
from config import (
    CLAIMS_CSV, SAMPLE_CLAIMS_CSV,
    USER_HISTORY_CSV, EVIDENCE_REQUIREMENTS_CSV,
)


def load_claims(csv_path=None) -> pd.DataFrame:
    """Load claims CSV into a DataFrame."""
    path = csv_path or CLAIMS_CSV
    df = pd.read_csv(path)
    return df


def load_user_history() -> Dict[str, dict]:
    """
    Load user_history.csv into a dict keyed by user_id.
    Each value is a dict of the row's columns.
    """
    df = pd.read_csv(USER_HISTORY_CSV)
    history = {}
    for _, row in df.iterrows():
        uid = row["user_id"]
        history[uid] = {
            "user_id": uid,
            "past_claim_count": int(row["past_claim_count"]),
            "accept_claim": int(row["accept_claim"]),
            "manual_review_claim": int(row["manual_review_claim"]),
            "rejected_claim": int(row["rejected_claim"]),
            "last_90_days_claim_count": int(row["last_90_days_claim_count"]),
            "history_flags": str(row.get("history_flags", "none")),
            "history_summary": str(row.get("history_summary", "")),
        }
    return history


def load_evidence_requirements() -> Dict[Tuple[str, str], dict]:
    """
    Load evidence_requirements.csv into a dict keyed by (claim_object, applies_to).
    Also stores entries with claim_object='all' separately for global rules.
    Returns a flat dict where each key maps to the row dict.
    """
    df = pd.read_csv(EVIDENCE_REQUIREMENTS_CSV)
    requirements = {}
    for _, row in df.iterrows():
        key = (str(row["claim_object"]).strip(), str(row["applies_to"]).strip())
        requirements[key] = {
            "requirement_id": str(row["requirement_id"]),
            "claim_object": str(row["claim_object"]),
            "applies_to": str(row["applies_to"]),
            "minimum_image_evidence": str(row["minimum_image_evidence"]),
        }
    return requirements


def get_relevant_requirements(claim_object: str, requirements: dict) -> list:
    """
    Get all evidence requirements relevant to a given claim_object.
    Includes both object-specific rules and 'all' rules.
    """
    relevant = []
    for (obj, applies_to), req in requirements.items():
        if obj == claim_object or obj == "all":
            relevant.append(req)
    return relevant
