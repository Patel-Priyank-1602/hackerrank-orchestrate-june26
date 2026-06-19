"""
Stage 6 — Output Builder

Takes all values from Stages 2–5 and assembles one row with exactly 14 columns
in the required order. Validates all fields against allowed values and applies
post-processing corrections for common model errors.
"""

from config import (
    ALLOWED_CLAIM_STATUS, ALLOWED_ISSUE_TYPES,
    ALLOWED_OBJECT_PARTS, ALLOWED_RISK_FLAGS,
    ALLOWED_SEVERITY, ALLOWED_BOOL,
    OUTPUT_COLUMNS,
)


def validate_claim_status(value: str) -> str:
    """Validate claim_status against allowed values."""
    v = str(value).strip().lower()
    return v if v in ALLOWED_CLAIM_STATUS else "not_enough_information"


def validate_issue_type(value: str) -> str:
    """Validate issue_type against allowed values."""
    v = str(value).strip().lower()
    if v in ALLOWED_ISSUE_TYPES:
        return v
    # Common model mistakes: map near-matches
    issue_map = {
        "shatter": "glass_shatter",
        "shattered": "glass_shatter",
        "broken": "broken_part",
        "missing": "missing_part",
        "torn": "torn_packaging",
        "crushed": "crushed_packaging",
        "water": "water_damage",
        "liquid_damage": "water_damage",
        "liquid": "stain",
        "scuff": "scratch",
        "scrape": "scratch",
        "paint_damage": "scratch",
        "fracture": "crack",
        "chip": "crack",
        "depression": "dent",
        "deformation": "dent",
        "tear": "torn_packaging",
        "rip": "torn_packaging",
    }
    return issue_map.get(v, "unknown")


def validate_object_part(value: str, claim_object: str) -> str:
    """Validate object_part against allowed values for the claim_object type."""
    v = str(value).strip().lower()
    allowed = ALLOWED_OBJECT_PARTS.get(claim_object, set())
    # Also check all object types for a match
    all_parts = set()
    for parts in ALLOWED_OBJECT_PARTS.values():
        all_parts |= parts
    
    if v in allowed:
        return v
    elif v in all_parts:
        return v  # Accept valid part from another category
    
    # Common model mistakes: map near-matches
    part_map = {
        "bumper": "front_bumper",
        "front bumper": "front_bumper",
        "rear bumper": "rear_bumper",
        "mirror": "side_mirror",
        "left_mirror": "side_mirror",
        "right_mirror": "side_mirror",
        "left_side_mirror": "side_mirror",
        "right_side_mirror": "side_mirror",
        "front_headlight": "headlight",
        "rear_taillight": "taillight",
        "back_light": "taillight",
        "front_glass": "windshield",
        "front_windshield": "windshield",
        "display": "screen",
        "lcd": "screen",
        "monitor": "screen",
        "keys": "keyboard",
        "keycap": "keyboard",
        "keycaps": "keyboard",
        "touchpad": "trackpad",
        "palm_rest": "trackpad",
        "top_cover": "lid",
        "top_lid": "lid",
        "outer_body": "body",
        "casing": "body",
        "chassis": "body",
        "edge": "corner",
        "side_edge": "corner",
        "box_corner": "package_corner",
        "corner": "package_corner" if claim_object == "package" else "corner",
        "side": "package_side" if claim_object == "package" else "body",
        "flap": "seal",
        "tape": "seal",
        "shipping_label": "label",
        "content": "contents",
        "product": "item",
        "inner_item": "item",
    }
    return part_map.get(v, "unknown")


def validate_severity(value: str) -> str:
    """Validate severity against allowed values."""
    v = str(value).strip().lower()
    return v if v in ALLOWED_SEVERITY else "unknown"


def validate_bool(value) -> str:
    """Validate boolean fields to 'true' or 'false' strings."""
    if isinstance(value, bool):
        return "true" if value else "false"
    v = str(value).strip().lower()
    return v if v in ALLOWED_BOOL else "false"


def validate_risk_flags(flags_str: str) -> str:
    """Validate each flag in the semicolon-separated risk_flags string."""
    if not flags_str or flags_str.strip().lower() == "none":
        return "none"
    
    flags = []
    for f in flags_str.split(";"):
        f = f.strip().lower()
        if f and f in ALLOWED_RISK_FLAGS and f != "none":
            flags.append(f)
    
    return ";".join(sorted(flags)) if flags else "none"


def validate_supporting_image_ids(ids_value, available_ids: list) -> str:
    """Validate supporting_image_ids."""
    if isinstance(ids_value, list):
        valid = [str(i) for i in ids_value if str(i).lower() != "none" and str(i).strip()]
        if not valid:
            return "none"
        return ";".join(valid)
    
    v = str(ids_value).strip()
    if v.lower() == "none" or not v:
        return "none"
    return v


def post_process_row(row: dict, parsed_claim: dict = None) -> dict:
    """
    Apply post-processing corrections to fix common model errors.
    This catches systematic issues that the vision model tends to make.
    """
    # Fix 1: If claim_status is "contradicted" or "supported", evidence_standard_met should be "true"
    # (You can only contradict or support a claim if you CAN see enough to make a judgment)
    if row["claim_status"] in ("contradicted", "supported"):
        row["evidence_standard_met"] = "true"
    
    # Fix 2: If claim_status is "contradicted" and issue_type is "none", severity should be "none"
    if row["claim_status"] == "contradicted" and row["issue_type"] == "none":
        row["severity"] = "none"
    
    # Fix 3: If valid_image is "false" but claim_status is "supported" or "contradicted",
    # the model was able to analyze something, so valid_image should be "true"
    # (Unless the contradiction is specifically about wrong/fake image)
    if row["valid_image"] == "false" and row["claim_status"] in ("supported",):
        row["valid_image"] = "true"
    
    # Fix 4: If object_part is "unknown" but parsed_claim has a specific part, use it
    if row["object_part"] == "unknown" and parsed_claim:
        claimed_parts = parsed_claim.get("claimed_object_parts", [])
        if claimed_parts and claimed_parts[0] != "unknown":
            candidate = claimed_parts[0].strip().lower()
            claim_object = row.get("claim_object", "")
            validated = validate_object_part(candidate, claim_object)
            if validated != "unknown":
                row["object_part"] = validated
    
    # Fix 5: If severity is "unknown" but issue_type is a specific damage type, 
    # and claim_status is supported, default to "medium"
    if row["severity"] == "unknown" and row["issue_type"] not in ("none", "unknown"):
        if row["claim_status"] == "supported":
            row["severity"] = "medium"
        elif row["claim_status"] == "contradicted":
            row["severity"] = "low"
    
    # Fix 6: If supporting_image_ids is "none" but claim_status is "supported",
    # use the first available image
    if row["supporting_image_ids"] == "none" and row["claim_status"] == "supported":
        # We can infer at least one image supported it
        pass  # Leave as-is, the model should have set this
    
    return row


def build_output_row(
    user_id: str,
    image_paths: str,
    user_claim: str,
    claim_object: str,
    vision_result: dict,
    risk_flags: str,
    available_image_ids: list,
    parsed_claim: dict = None,
) -> dict:
    """
    Assemble one validated output row from all pipeline stage results.
    Returns a dict with exactly the 14 required columns.
    """
    row = {
        "user_id": user_id,
        "image_paths": image_paths,
        "user_claim": user_claim,
        "claim_object": claim_object,
        "evidence_standard_met": validate_bool(
            vision_result.get("evidence_standard_met", True)
        ),
        "evidence_standard_met_reason": str(
            vision_result.get("evidence_standard_met_reason", "Unable to determine.")
        ).strip(),
        "risk_flags": validate_risk_flags(risk_flags),
        "issue_type": validate_issue_type(
            vision_result.get("issue_type", "unknown")
        ),
        "object_part": validate_object_part(
            vision_result.get("object_part", "unknown"), claim_object
        ),
        "claim_status": validate_claim_status(
            vision_result.get("claim_status", "not_enough_information")
        ),
        "claim_status_justification": str(
            vision_result.get("claim_status_justification", "Unable to determine.")
        ).strip(),
        "supporting_image_ids": validate_supporting_image_ids(
            vision_result.get("supporting_image_ids", ["none"]),
            available_image_ids,
        ),
        "valid_image": validate_bool(
            vision_result.get("valid_image", True)
        ),
        "severity": validate_severity(
            vision_result.get("severity", "unknown")
        ),
    }

    # Apply post-processing corrections
    row = post_process_row(row, parsed_claim)

    return row
