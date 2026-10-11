# ⚡ Saksham_AI: Real-Time LLM Prompt Coaching & Cost Intelligence Platform

> **"Stop burning tokens before you send."**
> A real-time pre-send coaching tool for AI prompts that shows token count, estimated API cost, and approximate environmental impact while you type. It scores efficiency, flags vague or redundant phrasing, suggests tighter rewrites with visual diffs, and recommends smaller models for simple tasks.

---

## 🌟 Executive Summary & Motivation

### The Problem
- **LLM usage is billed per token**, but developers and product teams cannot see what a prompt costs until after they send it.
- **Vague prompts trigger endless clarification loops**: Each follow-up message resends the entire conversation context window, multiplying token spend exponentially.
- **Model Overkill**: Developers frequently send tiny tasks (JSON extraction, formatting, regex, short classification) to massive flagship models like GPT-4o or Claude 3.5 Sonnet when compact models like GPT-4o-mini or Gemini 1.5 Flash would deliver identical results at **90–95% lower cost**.
- **The "Prevention Gap"**: Teams rely on post-facto billing dashboards at month-end. By then, the budget is already spent. **Saksham_AI introduces prevention at keystroke time.**

### Why It's a High-Impact Data & Analytics Project
- **Telemetry Collection**: Intercepts prompt events and captures granular usage telemetry.
- **Relational Data Modeling**: Stores prompt hashes, token volumes, cost metrics, efficiency scores, and department metadata in a structured SQL database.
- **Business Intelligence & Executive Insights**: Surfaces daily cost trends, savings realization, model distribution, and departmental budget leaderboards with direct Power BI / Excel CSV export capabilities.

---

## 📐 System Architecture

```
[Browser / Web Editor / IDE Plugin]
        │  (user types prompt, debounced ~300-500 ms)
        ▼
[FastAPI Gateway (:8000)]
   ├─ Token Counter  ────────► tiktoken (cl100k_base / o200k_base) + model calibration
   ├─ Cost Calculator ───────► Pricing tables (USD per 1M input & output tokens)
   ├─ Efficiency Scorer ─────► Weighted rule-based heuristic (0–100 score + diagnostics)
   ├─ Rewriter Engine ───────► Zero-cost deterministic compressor + word-level diff stream
   ├─ Model Recommender ─────► Task classifier (Simple vs Complex) + routing delta savings
   └─ Impact Estimator ──────► Tokens × energy-per-token (Wh) × grid carbon factor (g CO2e)
        │
        ▼
[Database: SQLite / PostgreSQL]  ← prompt_hash, tokens, cost, score, model, timestamp, team
        │
        ▼
[Analytics & BI Dashboard]  ← 30-day trends, savings realization, departmental reports, Power BI export
```

---

## 🚀 Key Features & How They Work

### 1. Token Counting
- Uses OpenAI's official `tiktoken` library (`o200k_base` for GPT-4o, `cl100k_base` for GPT-4/3.5) with calibrated multipliers for Claude and Gemini tokenizers.
- Delivers sub-millisecond local token counting before sending.
- Computes character counts, word counts, and token-to-word density ratios.

### 2. Cost Calculation
$$\text{Cost} = \frac{\text{Input Tokens} \times \text{Input Price} + \text{Expected Output Tokens} \times \text{Output Price}}{1,000,000}$$
- Maintained in dynamic pricing tables per 1M tokens across 10+ industry models (OpenAI, Anthropic, Google, Meta).
- Computes single-query cost, batch projections (10,000 & 1,000,000 invocations), and min/max bounds based on output elasticity.

### 3. Efficiency Scorer (0–100 Weighted Heuristic)
- **Conversational Fillers & Politeness Bloat (-5 to -25 pts)**: Flags useless preambles like *"Please kindly can you help me"* and *"Thank you in advance"*.
- **Vagueness (-10 to -25 pts)**: Flags unconstrained directives like *"Make it better"* or *"Fix it"* that lack clear acceptance criteria and trigger follow-up messages.
- **Redundancy (-10 to -20 pts)**: Identifies duplicated instructions and repeated constraints.
- **Missing Output Format (-10 pts)**: Flags prompts lacking schema boundaries (JSON, Markdown, tables).
- **Structure Bonuses (+5 to +15 pts)**: Rewards XML delimiters (`<context>`), markdown headers, and explicit negative constraints.

### 4. Tighter Prompt Rewrite & Visual Diff
- Deterministic, zero-cost local compression engine strips conversational filler and sharpens imperative directives without modifying intent or constraints.
- Generates word-level visual diffs (green additions, red strikethrough deletions).
- Calculates exact token reduction %, dollar savings per 10k calls, and a breakeven explanation.

### 5. Smart Model Routing Recommendation
- Classifies prompt intent into **Simple** (classification, JSON formatting, extraction), **Moderate** (summarization, standard drafting), or **Complex** (architecture design, multi-step proofs, concurrency).
- Suggests compact models (e.g., switching from GPT-4o to GPT-4o-mini) and calculates delta savings (e.g., **"Save 94% ($0.023 / call)"**).

### 6. Environmental & Carbon Footprint
- Calibrated using peer-reviewed publications:
  - **Luccioni et al. (2023)**: *Counting Carbon: A Survey of Carbon Footprints of Machine Learning*
  - **Patterson et al. (2021)**: *Carbon Emissions and Large Neural Network Training and Inference*
- Calculates energy consumption (Wh), carbon equivalent (g CO2e), water cooling footprint (mL), and tangible real-world equivalents (e.g., LED bulb runtime).

### 7. SQL Database & BI Analytics Dashboard
- Pre-seeded with 30 days of realistic multi-department usage data across Engineering, Data, and Product teams.
- Executive KPIs: Total Prompts, Total Spend, Total Savings Achieved, Average Efficiency, and Carbon Avoided.
- Interactive Chart.js visualizations (30-day savings trend line, model usage doughnut, team breakdown).
- Tabular audit log with search, team filtering, and 1-click **CSV Export for Power BI**.

---

## 💻 Tech Stack Justification

| Layer | Choice | Why |
|---|---|---|
| **Backend** | Python + FastAPI | High concurrency, native async speed, seamless integration with ML libraries. |
| **Tokenization** | `tiktoken` | Sub-millisecond pre-send counting matching OpenAI production tokenizers. |
| **Database** | SQLite (with PostgreSQL compatibility) | Lightweight relational storage with standard SQL aggregation for analytics. |
| **Frontend** | Vanilla HTML5 / Modern CSS / Vanilla JS | Zero build bloat, instantaneous loading, full control over Dribbble glassmorphic aesthetics. |
| **Data Visualization** | Chart.js | Interactive, responsive executive charts matching dark mode design tokens. |

---

## 🛠️ How to Run Locally

### Prerequisites
- Python 3.10+
- Virtual environment with dependencies installed:

```bash
# 1. Activate virtual environment
.\.venv\Scripts\activate   # On Windows
# or: source .venv/bin/activate on macOS/Linux

# 2. Run backend and serve frontend
python run_app.py
```

### 3. Open in Browser
Navigate to:
```
http://localhost:8000
```

---

## 🧪 Running Automated Tests

Run the test suite:
```bash
.\.venv\Scripts\python -m unittest tests/test_backend.py
```
All 7 unit tests cover token counting, cost calculations, efficiency scoring, heuristic rewriting, model recommendations, carbon estimation, and SQLite logging.

---

## 🎤 Interview Pitch & Talking Points

1. **The Prevention Gap**: *"Most enterprises have usage dashboards after the fact. Saksham_AI brings prevention into the typing flow, eliminating costly back-and-forth loops before money is spent."*
2. **The Analytics Link**: *"This is an end-to-end data project. It captures telemetry, models multi-dimensional cost structures, stores audit records in SQL, and serves executive BI metrics."*
3. **Deterministic vs LLM Trade-off**: *"Calling an LLM to evaluate every keystroke is economically unviable. We designed a deterministic, weighted rule-base running in &lt;1ms at zero API cost."*
