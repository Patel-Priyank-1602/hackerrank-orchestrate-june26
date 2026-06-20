# Evaluation Report — Multi-Modal Evidence Review

Generated: 2026-06-20T10:35:50.162898

---


## Strategy: Detailed Prompt (comprehensive system prompt with full context)

### Per-Column Accuracy

| Column | Type | Accuracy / Avg Score | Correct / Total |
|--------|------|---------------------|-----------------|
| `evidence_standard_met` | Exact Match | 90.0% | 18/20 |
| `evidence_standard_met_reason` | Text Overlap | 44.7% | 17/20 (≥30%) |
| `risk_flags` | Set Overlap | 61.1% | 14/20 (≥50%) |
| `issue_type` | Exact Match | 45.0% | 9/20 |
| `object_part` | Exact Match | 80.0% | 16/20 |
| `claim_status` | Exact Match | 70.0% | 14/20 |
| `claim_status_justification` | Text Overlap | 33.0% | 12/20 (≥30%) |
| `supporting_image_ids` | Set Overlap | 87.5% | 18/20 (≥50%) |
| `valid_image` | Exact Match | 90.0% | 18/20 |
| `severity` | Exact Match | 45.0% | 9/20 |

**Overall Average Score: 64.6%**


### Detailed Mismatches (Exact Match Columns)


#### `evidence_standard_met` — 2 mismatch(es)

| Row | Predicted | Expected |
|-----|-----------|----------|
| 1 | `false` | `True` |
| 7 | `false` | `True` |

#### `issue_type` — 11 mismatch(es)

| Row | Predicted | Expected |
|-----|-----------|----------|
| 0 | `broken_part` | `dent` |
| 1 | `unknown` | `scratch` |
| 2 | `glass_shatter` | `crack` |
| 3 | `crack` | `broken_part` |
| 4 | `dent` | `scratch` |
| 7 | `unknown` | `broken_part` |
| 8 | `glass_shatter` | `crack` |
| 12 | `glass_shatter` | `crack` |
| 13 | `scratch` | `none` |
| 18 | `none` | `unknown` |

#### `object_part` — 4 mismatch(es)

| Row | Predicted | Expected |
|-----|-----------|----------|
| 7 | `hood` | `front_bumper` |
| 15 | `package_side` | `seal` |
| 16 | `box` | `package_side` |
| 18 | `box` | `unknown` |

#### `claim_status` — 6 mismatch(es)

| Row | Predicted | Expected |
|-----|-----------|----------|
| 0 | `contradicted` | `supported` |
| 1 | `not_enough_information` | `supported` |
| 4 | `supported` | `contradicted` |
| 7 | `not_enough_information` | `contradicted` |
| 13 | `supported` | `contradicted` |
| 19 | `supported` | `contradicted` |

#### `valid_image` — 2 mismatch(es)

| Row | Predicted | Expected |
|-----|-----------|----------|
| 7 | `true` | `False` |
| 17 | `true` | `False` |

#### `severity` — 11 mismatch(es)

| Row | Predicted | Expected |
|-----|-----------|----------|
| 0 | `high` | `medium` |
| 1 | `unknown` | `low` |
| 2 | `high` | `medium` |
| 4 | `medium` | `low` |
| 7 | `unknown` | `high` |
| 8 | `high` | `medium` |
| 11 | `medium` | `low` |
| 12 | `high` | `medium` |
| 13 | `low` | `none` |
| 18 | `none` | `low` |

---

## Operational Analysis

- **Claims processed**: 20
- **Images processed**: 29
- **Total runtime**: 276.3s (13.8s per claim)
- **Model calls per claim**: 2 (1× text parser + 1× vision analyzer)
- **Total model calls**: 40
- **Approx input tokens**: ~40000 (text) + ~43500 (images)
- **Approx output tokens**: ~8000
- **Cost estimate (Groq free tier)**: $0.00 (free tier)
- **TPM/RPM strategy**: 30 RPM with 2s sleep between claims
- **Retry strategy**: Up to 3 retries with exponential backoff on 429 errors
- **Caching**: No caching implemented (each claim is unique)
- **Batching**: Single claim per API call (Groq does not support batch vision)
