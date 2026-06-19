# Multi-Modal Evidence Review — Solution

## Overview

A 6-stage pipeline that verifies damage claims using submitted images, claim conversation text, user history, and evidence requirements.

## Architecture

```
Stage 1 — Load Inputs
  ↓ claims.csv, user_history.csv, evidence_requirements.csv
Stage 2 — Claim Text Parsing
  ↓ llama-3.3-70b-versatile on Groq (extract damage type, parts, suspicious language)
Stage 3 — Encode Images
  ↓ Python base64 + Pillow (convert to data URLs)
Stage 4 — Vision Analysis (Core)
  ↓ llama-4-scout-17b-16e-instruct on Groq (image validity, evidence check, damage detection)
Stage 5 — Risk Engine
  ↓ Pure Python (combine image flags + history flags)
Stage 6 — Output Builder
  ↓ pandas (validate all 14 columns, write CSV)
```

## Setup

### 1. Install dependencies
```bash
cd code
pip install -r requirements.txt
```

### 2. Set your Groq API key
```bash
# Option A: Environment variable
export GROQ_API_KEY=your_key_here

# Option B: Create .env file in code/ directory
cp .env.example .env
# Edit .env and add your key
```

### 3. Get a free Groq API key
Go to [console.groq.com](https://console.groq.com) → Create API Key

## Usage

### Process test claims (produce output.csv)
```bash
cd code
python main.py
```

### Process sample claims (for evaluation)
```bash
cd code
python main.py --sample
```

### Run evaluation
```bash
cd code
python evaluation/main.py
```

### Custom input/output
```bash
cd code
python main.py --input path/to/claims.csv --output path/to/output.csv
```

## File Structure

```
code/
├── main.py               # Pipeline orchestrator (entry point)
├── config.py             # Configuration, paths, allowed values
├── loader.py             # Stage 1: Data loading
├── text_parser.py        # Stage 2: Claim text parsing (Groq LLM)
├── image_encoder.py      # Stage 3: Image base64 encoding
├── vision_analyzer.py    # Stage 4: Vision analysis (Groq VLM)
├── risk_engine.py        # Stage 5: Risk flag computation
├── output_builder.py     # Stage 6: Output validation & assembly
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variable template
├── README.md             # This file
└── evaluation/
    └── main.py           # Evaluation script
```

## Models Used

| Model | Purpose | Provider |
|-------|---------|----------|
| `llama-3.3-70b-versatile` | Text parsing (Stage 2) | Groq (free tier) |
| `meta-llama/llama-4-scout-17b-16e-instruct` | Vision analysis (Stage 4) | Groq (free tier) |

## Rate Limiting

- 2-second delay between claims to stay under Groq's ~30 RPM limit for vision
- Automatic retry with exponential backoff on 429 errors (up to 3 retries)
- Text model has more generous limits

## Output Format

14 columns in exact order: `user_id`, `image_paths`, `user_claim`, `claim_object`, `evidence_standard_met`, `evidence_standard_met_reason`, `risk_flags`, `issue_type`, `object_part`, `claim_status`, `claim_status_justification`, `supporting_image_ids`, `valid_image`, `severity`

All values are validated against the allowed value sets defined in the problem statement.
