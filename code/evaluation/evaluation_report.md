# Evaluation Report — Multi-Modal Evidence Review

Generated: 2026-06-19T13:03:26.268490

---


## Strategy: Detailed Prompt (comprehensive system prompt with full context)

### Per-Column Accuracy

| Column | Type | Accuracy / Avg Score | Correct / Total |
|--------|------|---------------------|-----------------|
| `evidence_standard_met` | Exact Match | 50.0% | 10/20 |
| `evidence_standard_met_reason` | Text Overlap | 22.0% | 9/20 (≥30%) |
| `risk_flags` | Set Overlap | 63.9% | 12/20 (≥50%) |
| `issue_type` | Exact Match | 45.0% | 9/20 |
| `object_part` | Exact Match | 65.0% | 13/20 |
| `claim_status` | Exact Match | 55.0% | 11/20 |
| `claim_status_justification` | Text Overlap | 25.9% | 11/20 (≥30%) |
| `supporting_image_ids` | Set Overlap | 65.0% | 13/20 (≥50%) |
| `valid_image` | Exact Match | 70.0% | 14/20 |
| `severity` | Exact Match | 45.0% | 9/20 |

**Overall Average Score: 50.7%**


### Detailed Mismatches (Exact Match Columns)


#### `evidence_standard_met` — 10 mismatch(es)

| Row | Predicted | Expected |
|-----|-----------|----------|
| 0 | `false` | `True` |
| 1 | `false` | `True` |
| 6 | `false` | `True` |
| 7 | `false` | `True` |
| 9 | `false` | `True` |
| 13 | `false` | `True` |
| 14 | `false` | `True` |
| 15 | `false` | `True` |
| 18 | `false` | `True` |
| 19 | `false` | `True` |

#### `issue_type` — 11 mismatch(es)

| Row | Predicted | Expected |
|-----|-----------|----------|
| 1 | `dent` | `scratch` |
| 4 | `dent` | `scratch` |
| 5 | `none` | `unknown` |
| 7 | `dent` | `broken_part` |
| 10 | `water_damage` | `stain` |
| 12 | `glass_shatter` | `crack` |
| 13 | `unknown` | `none` |
| 14 | `unknown` | `crushed_packaging` |
| 15 | `unknown` | `torn_packaging` |
| 16 | `stain` | `water_damage` |

#### `object_part` — 7 mismatch(es)

| Row | Predicted | Expected |
|-----|-----------|----------|
| 5 | `unknown` | `headlight` |
| 13 | `unknown` | `trackpad` |
| 14 | `unknown` | `package_corner` |
| 15 | `unknown` | `seal` |
| 16 | `box` | `package_side` |
| 17 | `unknown` | `contents` |
| 19 | `unknown` | `seal` |

#### `claim_status` — 9 mismatch(es)

| Row | Predicted | Expected |
|-----|-----------|----------|
| 0 | `contradicted` | `supported` |
| 1 | `not_enough_information` | `supported` |
| 4 | `supported` | `contradicted` |
| 6 | `not_enough_information` | `supported` |
| 13 | `not_enough_information` | `contradicted` |
| 14 | `not_enough_information` | `supported` |
| 15 | `not_enough_information` | `supported` |
| 18 | `not_enough_information` | `contradicted` |
| 19 | `not_enough_information` | `contradicted` |

#### `valid_image` — 6 mismatch(es)

| Row | Predicted | Expected |
|-----|-----------|----------|
| 5 | `false` | `True` |
| 13 | `false` | `True` |
| 14 | `false` | `True` |
| 15 | `false` | `True` |
| 18 | `false` | `True` |
| 19 | `false` | `True` |

#### `severity` — 11 mismatch(es)

| Row | Predicted | Expected |
|-----|-----------|----------|
| 0 | `high` | `medium` |
| 1 | `unknown` | `low` |
| 2 | `high` | `medium` |
| 4 | `medium` | `low` |
| 8 | `high` | `medium` |
| 12 | `high` | `medium` |
| 13 | `unknown` | `none` |
| 14 | `unknown` | `medium` |
| 15 | `unknown` | `medium` |
| 18 | `unknown` | `low` |

---

## Operational Analysis

- **Claims processed**: 20
- **Images processed**: 29
- **Total runtime**: 605.2s (30.3s per claim)
- **Model calls per claim**: 2 (1× text parser + 1× vision analyzer)
- **Total model calls**: 40
- **Approx input tokens**: ~40000 (text) + ~43500 (images)
- **Approx output tokens**: ~8000
- **Cost estimate (Groq free tier)**: $0.00 (free tier)
- **TPM/RPM strategy**: 30 RPM with 2s sleep between claims
- **Retry strategy**: Up to 3 retries with exponential backoff on 429 errors
- **Caching**: No caching implemented (each claim is unique)
- **Batching**: Single claim per API call (Groq does not support batch vision)
