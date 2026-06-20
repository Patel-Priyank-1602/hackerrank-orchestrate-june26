# 🚀 HackerRank Orchestrate (June 2026)!

<div align="center">
  <img src="https://img.shields.io/badge/Status-Completed-success?style=for-the-badge" alt="Status" />
  <img src="https://img.shields.io/badge/Language-Python-blue?style=for-the-badge&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/AI-Multi--Modal-purple?style=for-the-badge" alt="AI Multi-Modal" />
</div>

<br />

Welcome to the ultimate **Multi-Modal Evidence Review System** built for the HackerRank Orchestrate 24-hour hackathon! This project seamlessly verifies damage claims using a combination of image evidence, user chat transcripts, and historical risk contexts.

## 🌟 Approach & Architecture
Our system leverages advanced visual and linguistic models to accurately cross-reference user claims against actual submitted imagery.

**Core Highlights:**
- **Dynamic Risk Engine:** Evaluates past user behavior alongside current claims to flag potential anomalies.
- **Vision Analyzer:** Extracts key features from images to check for specific object parts and visible damage.
- **Intelligent Evaluation Workflow:** Correlates chat logs and visual cues to yield a definitive status: `supported`, `contradicted`, or `not_enough_information`.

## 🔄 Execution Sequence Diagram

Here is an end-to-end flow of how the system processes a user claim:

```mermaid
sequenceDiagram
    participant User
    participant System as Evidence Review System
    participant Risk as Risk Engine
    participant Vision as Vision Analyzer
    participant Output as Output Builder

    User->>System: Submit Claim (Chat + Images)
    System->>Risk: Fetch User History
    Risk-->>System: Return Risk Flags & Context
    
    System->>Vision: Send Image(s) + Object Type
    Vision-->>System: Return Image Features & Damage Severity
    
    System->>System: Validate Evidence Standard (Rules Layer)
    
    alt Evidence Standard Met
        System->>System: Correlate Chat Transcript with Image Features
        alt Claim Matches Evidence
            System->>Output: Generate Status "supported"
        else Claim Contradicts Evidence
            System->>Output: Generate Status "contradicted"
        end
    else Standard Not Met
        System->>Output: Generate Status "not_enough_information"
    end
    
    Output-->>User: Return Structured Predictions (output.csv)
```

## 🛠️ Quick Setup Instructions

1. **Clone & CD:**
   ```bash
   git clone git@github.com:interviewstreet/hackerrank-orchestrate-june26.git
   cd hackerrank-orchestrate-june26
   ```

2. **Environment Setup:**
   Ensure you have your environment variables ready:
   ```bash
   cp code/.env.example code/.env
   # Add your API keys to the .env file
   ```

3. **Install Dependencies:**
   ```bash
   cd code
   pip install -r requirements.txt
   ```

4. **Run the Solution:**
   ```bash
   python main.py
   ```

5. **Evaluate:**
   ```bash
   python evaluation/main.py
   ```

## 📈 Evaluation & Results
All evaluations are documented and thoroughly analyzed inside the `code/evaluation/evaluation_report.md` file.

Made with ❤️ and extreme engineering by the Developer.
