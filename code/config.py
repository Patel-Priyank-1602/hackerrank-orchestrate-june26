"""
Configuration module for the Multi-Modal Evidence Review system.
Centralizes all constants, allowed values, model names, and paths.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ─── API Configuration ───────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ─── Model Configuration ─────────────────────────────────────────────────────
TEXT_MODEL = "llama-3.3-70b-versatile"          # For claim text parsing (Stage 2)
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"  # For vision analysis (Stage 4)

# ─── Rate Limiting ────────────────────────────────────────────────────────────
SLEEP_BETWEEN_CLAIMS = 2        # Seconds between each claim to avoid rate limits
RETRY_DELAY_ON_429 = 10         # Seconds to wait on 429 (rate limit) error
MAX_RETRIES = 3                 # Maximum retries per API call

# ─── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "dataset"
CLAIMS_CSV = DATASET_DIR / "claims.csv"
SAMPLE_CLAIMS_CSV = DATASET_DIR / "sample_claims.csv"
USER_HISTORY_CSV = DATASET_DIR / "user_history.csv"
EVIDENCE_REQUIREMENTS_CSV = DATASET_DIR / "evidence_requirements.csv"
IMAGES_DIR = DATASET_DIR / "images"
OUTPUT_CSV = PROJECT_ROOT / "output.csv"

# ─── Output Columns (exact order required) ────────────────────────────────────
OUTPUT_COLUMNS = [
    "user_id",
    "image_paths",
    "user_claim",
    "claim_object",
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

# ─── Allowed Values ──────────────────────────────────────────────────────────
ALLOWED_CLAIM_STATUS = {"supported", "contradicted", "not_enough_information"}

ALLOWED_ISSUE_TYPES = {
    "dent", "scratch", "crack", "glass_shatter", "broken_part",
    "missing_part", "torn_packaging", "crushed_packaging",
    "water_damage", "stain", "none", "unknown",
}

ALLOWED_OBJECT_PARTS = {
    "car": {
        "front_bumper", "rear_bumper", "door", "hood", "windshield",
        "side_mirror", "headlight", "taillight", "fender",
        "quarter_panel", "body", "unknown",
    },
    "laptop": {
        "screen", "keyboard", "trackpad", "hinge", "lid",
        "corner", "port", "base", "body", "unknown",
    },
    "package": {
        "box", "package_corner", "package_side", "seal",
        "label", "contents", "item", "unknown",
    },
}

ALLOWED_RISK_FLAGS = {
    "none", "blurry_image", "cropped_or_obstructed", "low_light_or_glare",
    "wrong_angle", "wrong_object", "wrong_object_part", "damage_not_visible",
    "claim_mismatch", "possible_manipulation", "non_original_image",
    "text_instruction_present", "user_history_risk", "manual_review_required",
}

ALLOWED_SEVERITY = {"none", "low", "medium", "high", "unknown"}

ALLOWED_BOOL = {"true", "false"}
